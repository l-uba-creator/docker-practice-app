"""
Динамический ETL DAG (финальный проект модуля «Автоматизация и деплой»).

Идея: бизнес хочет быстро добавлять новые агрегаты. Вместо правки DAG под
каждый агрегат, DAG ГЕНЕРИРУЕТСЯ из Python-словаря `CONFIG` (см.
config/tables_config.py). Чтобы добавить новый агрегат, достаточно дописать
один словарь в CONFIG — при следующем парсинге DAG автоматически построит
под него цепочку:

    [create_table] >> [load_data] >> [quality_check] >> [export_to_s3]

Требования задания покрыты так:
  1. Динамическая генерация Task'ов по словарям          -> цикл по CONFIG
     + TaskGroup на каждую таблицу (читаемость графа).
  2. Идемпотентность и качество наполнения данных:
       - DDL через CREATE TABLE IF NOT EXISTS            -> create_table
       - DML обёрнут в TRUNCATE + INSERT (одна транзакция)-> load_data
       - SQL-проверка качества (опц.)                    -> quality_check
  3. Авто-создание таблицы при добавлении нового агрегата-> create_table
     выполняется всегда, таблица создаётся автоматически.
  4. Опциональная выгрузка в объектное хранилище (CSV)   -> export_to_s3,
     добавляется только когда need_to_export = True.

Документация Airflow:
- Управление DAG: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html
- Динамические DAG: https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dagfile.html#creating-dags-dynamically-from-external-config
- TaskGroup: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#taskgroups
- Jinja-макросы: https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html
"""

from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.utils.task_group import TaskGroup

from config.tables_config import CONFIG

# Кастомные операторы регистрируются плагином; импортируем напрямую,
# чтобы DAG был самодостаточным для чтения и тестирования.
from operators.create_table_operator import PostgresCreateTableOperator
from operators.data_quality_operator import PostgresDataQualityOperator
from operators.export_to_s3_operator import PostgresToS3CSVOperator
from operators.load_table_operator import PostgresLoadTableOperator

# --- Параметры подключения (Airflow Connections) -------------------------
# Их нужно создать в UI: Admin -> Connections
#   - conn_id="pg_warehouse",  type=Postgres, host=db, schema=warehouse,
#     login=airflow, password=airflow, port=5432
#   - conn_id="s3_minio", type=AWS, extra={"endpoint_url": "http://minio:9000",
#     "aws_access_key_id":"minio","aws_secret_access_key":"minio123"}
PG_CONN_ID = "pg_warehouse"
S3_CONN_ID = "s3_minio"
S3_BUCKET = "exports"
S3_KEY_PREFIX = "dm"

DEFAULT_ARGS = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": pendulum.duration(minutes=2),
}

with DAG(
    dag_id="dynamic_etl_dag",
    description="Динамическая генерация ETL-задач по конфигу (Python-словарь).",
    default_args=DEFAULT_ARGS,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="@daily",
    catchup=False,
    max_active_tasks=1,  # пишем в одни и те же таблицы — сериализуем загрузку
    tags=["etl", "dynamic", "postgres", "s3"],
    doc_md=__doc__,
) as dag:

    # Глобальный сенсор готовности сырых данных (опц.): ждём, пока в
    # raw-слое появились строки за логический день. Все агрегаты стартуют
    # только после готовности источника.
    from airflow.sensors.sql import SqlSensor

    wait_for_raw = SqlSensor(
        task_id="wait_for_raw_payments",
        conn_id=PG_CONN_ID,
        sql=(
            "SELECT count(*) > 0 FROM raw_payments "
            "WHERE created_at::date = date '{{ ds }}'"
        ),
        poke_interval=30,
        timeout=60 * 10,
        mode="reschedule",
    )

    # --- ДИНАМИЧЕСКАЯ ГЕНЕРАЦИЯ ЗАДАЧ ПО КОНФИГУ --------------------------
    # Ключевой момент задания: задачи создаются в цикле по CONFIG.
    # Новый словарь == новая TaskGroup со всем пайплайном автоматически.
    for item in CONFIG:
        table = item["table_name"]

        with TaskGroup(group_id=f"load_{table}") as tg:

            create_table = PostgresCreateTableOperator(
                task_id=f"create_{table}",
                postgres_conn_id=PG_CONN_ID,
                ddl=item["table_ddl"],
            )

            load_data = PostgresLoadTableOperator(
                task_id=f"fill_{table}",
                postgres_conn_id=PG_CONN_ID,
                table_name=table,
                dml=item["table_dml"],
            )

            # Опциональная проверка качества (если задан блок `quality`).
            quality_cfg = item.get("quality")
            if quality_cfg:
                quality_check = PostgresDataQualityOperator(
                    task_id=f"check_{table}",
                    postgres_conn_id=PG_CONN_ID,
                    check_sql=quality_cfg["check_sql"],
                    fail_on=quality_cfg.get("fail_on", True),
                )
                load_data >> quality_check
                tail = quality_check
            else:
                tail = load_data

            # Опциональная выгрузка в объектное хранилище (CSV).
            # Добавляется ТОЛЬКО когда need_to_export = True.
            if item.get("need_to_export"):
                export = PostgresToS3CSVOperator(
                    task_id=f"export_{table}",
                    postgres_conn_id=PG_CONN_ID,
                    aws_conn_id=S3_CONN_ID,
                    table_name=table,
                    s3_bucket=S3_BUCKET,
                    s3_key_prefix=S3_KEY_PREFIX,
                    ds="{{ ds }}",
                )
                tail >> export

            # Внутри TaskGroup: create >> load >> [check] >> [export]
            create_table >> load_data

        # Сырой слой должен быть готов до старта любой группы агрегатов.
        wait_for_raw >> tg
