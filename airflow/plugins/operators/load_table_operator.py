"""
Идемпотентный оператор наполнения таблицы данными (DML).

Логика (в одной транзакции):
    BEGIN;
        TRUNCATE TABLE <table_name>;          -- очищаем партицию/таблицу
        INSERT INTO <table_name> <table_dml>;  -- перезаливаем агрегат
    COMMIT;

Почему TRUNCATE + INSERT, а не "INSERT ... ON CONFLICT"?
  - `table_dml` — это SELECT, формирующий агрегат; ON CONFLICT потребовал бы
    знания всех конфликтующих колонок, что снижает универсальность.
  - TRUNCATE + INSERT гарантирует, что при повторном запуске (тот же logical_date)
    в таблице окажется ровно тот же результат без дублей — это и есть
    идемпотентность наполнения.

Jinja-макросы в `table_dml` ({{ ds }}, {{ data_interval_start }}, ...) рендерятся
стандартным механизмом Airflow (template_fields).

Документация:
- https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html
- https://www.postgresql.org/docs/current/sql-truncate.html
"""

from __future__ import annotations

from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


class PostgresLoadTableOperator(BaseOperator):
    """Идемпотентно наполняет таблицу результатом DML-запроса."""

    template_fields = ("dml",)

    def __init__(
        self,
        postgres_conn_id: str,
        table_name: str,
        dml: str,
        truncate: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.postgres_conn_id = postgres_conn_id
        self.table_name = table_name
        self.dml = dml
        self.truncate = truncate

    def execute(self, context) -> int:
        hook = PostgresHook(postgres_conn_id=self.postgres_conn_id)

        insert_sql = f"INSERT INTO {self.table_name}\n{self.dml}"
        statements: list[str] = []
        if self.truncate:
            statements.append(f"TRUNCATE TABLE {self.table_name};")
        statements.append(insert_sql + ";")

        # hook.run со списком выполнит всё в одной транзакции (один commit).
        hook.run(statements, autocommit=False)

        row_count = hook.get_first(
            f"SELECT count(*) FROM {self.table_name}"
        )[0]
        self.log.info("Table %s loaded: %s rows", self.table_name, row_count)
        return int(row_count)
