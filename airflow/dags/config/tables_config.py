"""
Конфигурация таблиц для динамической генерации DAG.

Каждый элемент списка — это описание одного агрегата (таблицы), который DAG
должен автоматически:
  1. создать в БД            -> поле `table_ddl`  (CREATE TABLE IF NOT EXISTS ...)
  2. наполнить данными       -> поле `table_dml`  (SELECT ... с поддержкой Jinja)
  3. проверить качество      -> поле `quality`   (опц., SQL-проверка)
  4. выгрузить в S3 (CSV)    -> флаг `need_to_export` (True/False)

Чтобы добавить НОВЫЙ агрегат — достаточно дописать сюда один словарь.
DAG при следующем парсинге автоматически создаст под него отдельную
TaskGroup: create_table -> load_data -> quality_check -> [export_to_s3].

Поддержка макросов Jinja: в `table_dml` можно использовать {{ ds }},
{{ data_interval_start }}, {{ run_id }} и т.п. (см. документацию Airflow
по макросам: https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html).
"""

from __future__ import annotations

CONFIG: list[dict] = [
    {
        "table_name": "dm_payments_daily",
        "table_ddl": """
            CREATE TABLE IF NOT EXISTS dm_payments_daily (
                dt           date       NOT NULL,
                category     varchar(64) NOT NULL,
                amount       numeric(18,2) NOT NULL DEFAULT 0,
                tx_count     integer    NOT NULL DEFAULT 0,
                loaded_at    timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY (dt, category)
            )
        """,
        # Jinja-макрос {{ ds }} подставит дату логического дня выполнения DAG.
        # Идемпотентность обеспечивается оператором: TRUNCATE + INSERT.
        "table_dml": """
            SELECT
                created_at::date                       AS dt,
                category,
                sum(amount)                            AS amount,
                count(*)                               AS tx_count
            FROM raw_payments
            WHERE created_at::date = date '{{ ds }}'
            GROUP BY 1, 2
        """,
        "quality": {
            # Проверка, что за день есть хотя бы одна строка и нет NULL в ключах.
            "check_sql": """
                SELECT count(*) = 0 OR count(category) <> count(*)
                FROM dm_payments_daily WHERE dt = date '{{ ds }}'
            """,
            "fail_on": True,  # True -> оператор упадёт, если check_sql вернёт True
        },
        "need_to_export": True,
    },
    {
        "table_name": "dm_users_summary",
        "table_ddl": """
            CREATE TABLE IF NOT EXISTS dm_users_summary (
                category     varchar(64) NOT NULL,
                users_cnt    integer    NOT NULL DEFAULT 0,
                avg_balance numeric(18,2),
                loaded_at    timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY (category)
            )
        """,
        "table_dml": """
            SELECT
                category,
                count(*)                               AS users_cnt,
                avg(balance)                           AS avg_balance
            FROM raw_users
            GROUP BY 1
        """,
        "quality": {
            "check_sql": "SELECT count(*) = 0 FROM dm_users_summary",
            "fail_on": True,
        },
        "need_to_export": False,
    },
    {
        "table_name": "dm_top_categories",
        "table_ddl": """
            CREATE TABLE IF NOT EXISTS dm_top_categories (
                rank         integer    NOT NULL,
                category     varchar(64) NOT NULL,
                total        numeric(18,2) NOT NULL DEFAULT 0,
                loaded_at    timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY (rank)
            )
        """,
        "table_dml": """
            SELECT
                row_number() OVER (ORDER BY sum(amount) DESC) AS rank,
                category,
                sum(amount)                                    AS total
            FROM raw_payments
            GROUP BY 1
        """,
        "quality": None,
        "need_to_export": True,
    },
]
