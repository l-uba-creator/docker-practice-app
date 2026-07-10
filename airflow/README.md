# Финальный проект модуля «Автоматизация и деплой» — Airflow

Практическая работа по курсу **«Аналитика и инженерия данных»**.
Бизнес-кейс: нужно быстро добавлять новые агрегаты без правки DAG под каждый.
Решение — **динамическая генерация задач DAG по Python-словарю** (`CONFIG`).

Репозиторий курса: [github.com/l-uba-creator/docker-practice-app](https://github.com/l-uba-creator/docker-practice-app)

---

## Суть решения

В [`dags/config/tables_config.py`](dags/config/tables_config.py) лежит список
словарей `CONFIG`. Каждый словарь описывает один агрегат:

| Поле            | Назначение                                                         |
|-----------------|-------------------------------------------------------------------|
| `table_name`    | Имя таблицы-агрегата.                                              |
| `table_ddl`     | `CREATE TABLE IF NOT EXISTS …` — авто-создание таблицы.            |
| `table_dml`     | `SELECT …` с поддержкой Jinja-макросов (`{{ ds }}` и т.п.).        |
| `quality`       | (опц.) SQL-проверка качества данных.                              |
| `need_to_export`| `True/False` — выгружать результат в объектное хранилище (CSV).    |

Главный DAG — [`dags/dynamic_etl_dag.py`](dags/dynamic_etl_dag.py) — **в цикле
по `CONFIG`** строит для каждой таблицы `TaskGroup`:

```
wait_for_raw (SqlSensor) ─┐
                          ├─▶ load_<table> ─ create_table ─▶ fill_table ─▶ [check_table] ─▶ [export_table]
                          └─▶ load_<table_2> ─ …
```

Чтобы **добавить новый агрегат**, достаточно дописать один словарь в `CONFIG`.
При следующем парсинге DAG автоматически:
1. создаст таблицу (`CREATE TABLE IF NOT EXISTS`);
2. наполнит её данными (`TRUNCATE + INSERT`);
3. прогонит проверку качества (если задана);
4. выгрузит CSV в S3/MinIO (если `need_to_export = True`).

## Как покрыты требования задания

1. **Динамическая генерация Task'ов по словарям** — цикл `for item in CONFIG`
   + `TaskGroup` на каждую таблицу для читаемого графа.
2. **Идемпотентность и качество наполнения данных**:
   - DDL — `CREATE TABLE IF NOT EXISTS` → повторный запуск не падает;
   - DML обёрнут в одну транзакцию `TRUNCATE + INSERT` → при повторном
     запуске за тот же `ds` в таблице будет ровно тот же результат без дублей;
   - опциональная SQL-проверка качества (`PostgresDataQualityOperator`)
     падает при невыполнении условий и блокирует downstream-выгрузку.
3. **Авто-создание таблицы при добавлении** — задача `create_table`
   выполняется всегда, поэтому новая таблица создаётся автоматически.
4. **Опциональная выгрузка в объектное хранилище (CSV)** —
   `PostgresToS3CSVOperator` добавляется только когда `need_to_export = True`.

## Кастомные операторы (`plugins/operators/`)

| Оператор | Назначение |
|---|---|
| `PostgresCreateTableOperator` | Идемпотентное выполнение DDL (`CREATE TABLE IF NOT EXISTS`). |
| `PostgresLoadTableOperator` | `TRUNCATE + INSERT … <dml>` в одной транзакции; рендерит Jinja. |
| `PostgresDataQualityOperator` | SQL-предикат качества; падает при `fail_on`. |
| `PostgresToS3CSVOperator` | `COPY … TO STDOUT CSV HEADER` → загрузка в S3/MinIO. |

Все операторы корректно объявляют `template_fields`, чтобы Jinja-макросы
(`{{ ds }}`, `{{ data_interval_start }}`, `{{ run_id }}`) рендерились
стандартным механизмом Airflow.

## Запуск локально (Docker Compose)

Поднимает Airflow (LocalExecutor) + PostgreSQL + MinIO:

```bash
cd airflow
docker compose up -d --build

# инициализация БД и пользователя Airflow (выполняется в airflow-init автоматически)
# открыть UI:  http://localhost:8080   (admin / admin)
# MinIO:       http://localhost:9001   (minio / minio123)

# создать Connections для DAG:
docker compose exec airflow-scheduler bash /opt/airflow/scripts/setup_connections.sh
```

Connections создаются в `Admin → Connections`:
- `pg_warehouse` — Postgres, `postgres:5432/warehouse`, `airflow/airflow`;
- `s3_minio` — AWS, `extra={"endpoint_url":"http://minio:9000","region_name":"us-east-1"}`.

Сырой слой (`raw_payments`, `raw_users`) и демо-данные создаются скриптом
[`sql/init_raw.sql`](sql/init_raw.sql) при старте PostgreSQL.

## Тесты

```bash
cd airflow && python -m pytest tests/ -v
```

Проверяют форму конфига, уникальность имён таблиц, наличие хотя бы одной
таблицы с `need_to_export=True` и `False`, а также синтаксис DAG-файла.

## Структура каталога

```
airflow/
├── dags/
│   ├── dynamic_etl_dag.py        # основной DAG (динамическая генерация задач)
│   └── config/
│       └── tables_config.py      # Python-словарь CONFIG — источник правды
├── plugins/
│   ├── dynamic_etl_plugin.py     # регистрация операторов
│   └── operators/
│       ├── create_table_operator.py
│       ├── load_table_operator.py
│       ├── data_quality_operator.py
│       └── export_to_s3_operator.py
├── sql/
│   └── init_raw.sql              # raw-источник + демо-данные
├── tests/
│   └── test_dag_structure.py
├── scripts/
│   └── setup_connections.sh
├── docker-compose.yml            # Airflow + Postgres + MinIO
├── Dockerfile.airflow
├── requirements.txt
└── README.md
```

## Документация Airflow

- [Managing DAGs — Airflow Docs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html)
- [Creating DAGs dynamically from external config](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dagfile.html#creating-dags-dynamically-from-external-config)
- [TaskGroups](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html#taskgroups)
- [Jinja macros / templates-ref](https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html)
- [SqlSensor](https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/sensors/sql/index.html)
- [Data quality in Airflow](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/data-quality.html)
- [Postgres provider](https://airflow.apache.org/docs/apache-airflow-providers-postgres/stable/index.html)
- [Amazon provider (S3Hook)](https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/index.html)
- [PostgreSQL CREATE TABLE](https://www.postgresql.org/docs/current/sql-createtable.html)
- [PostgreSQL TRUNCATE](https://www.postgresql.org/docs/current/sql-truncate.html)
- [PostgreSQL COPY](https://www.postgresql.org/docs/current/sql-copy.html)
