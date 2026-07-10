"""
Идемпотентный оператор создания таблицы в PostgreSQL.

Выполняет `table_ddl` (как правило CREATE TABLE IF NOT EXISTS ...).
Благодаря IF NOT EXISTS повторный запуск не падает и не пересоздаёт схему —
это базовая гарантия идемпотентности: сколько бы раз DAG ни отработал,
структура таблицы остаётся стабильной.

Документация:
- https://airflow.apache.org/docs/apache-airflow-providers-postgres/stable/_api/airflow/providers/postgres/operators/postgres/index.html
- https://www.postgresql.org/docs/current/sql-createtable.html
"""

from __future__ import annotations

from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


class PostgresCreateTableOperator(BaseOperator):
    """Создаёт таблицу в БД по DDL из конфига (идемпотентно)."""

    template_fields = ("ddl",)
    template_fields_renderers = {"ddl": "sql"}

    def __init__(
        self,
        postgres_conn_id: str,
        ddl: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.postgres_conn_id = postgres_conn_id
        self.ddl = ddl

    def execute(self, context) -> str:
        hook = PostgresHook(postgres_conn_id=self.postgres_conn_id)
        # autocommit=True: DDL в PostgreSQL неявно коммитится, но
        # явный autocommit избавляет от лишней транзакционной обёртки.
        hook.run(self.ddl, autocommit=True)
        return "table ensured"
