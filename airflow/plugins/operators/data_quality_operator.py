"""
Оператор проверки качества данных (data quality check).

Выполняет `check_sql`, который должен вернуть булево (TRUE/FALSE) или
0/1. Если результат равен значению `fail_on` (по умолчанию True) — оператор
падает, что блокирует downstream (в т.ч. выгрузку в S3).

Пример check_sql (падает, если за день нет строк или есть NULL в ключах):
    SELECT count(*) = 0 OR count(category) <> count(*)
    FROM dm_payments_daily WHERE dt = date '{{ ds }}'

Документация:
- https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/data-quality.html
"""

from __future__ import annotations

from typing import Any

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


class PostgresDataQualityOperator(BaseOperator):
    """Проверяет качество данных простым SQL-предикатом."""

    template_fields = ("check_sql",)

    def __init__(
        self,
        postgres_conn_id: str,
        check_sql: str,
        fail_on: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.postgres_conn_id = postgres_conn_id
        self.check_sql = check_sql
        self.fail_on = fail_on

    def execute(self, context) -> Any:
        hook = PostgresHook(postgres_conn_id=self.postgres_conn_id)
        result = hook.get_first(self.check_sql)[0]

        # Приводим к bool: PostgreSQL может вернуть True/False, 0/1, t/f.
        if isinstance(result, str):
            failed = result.lower() in ("t", "true", "1")
        else:
            failed = bool(result)

        if failed == self.fail_on:
            raise AirflowException(
                f"Data quality check FAILED for task '{self.task_id}'. "
                f"check_sql returned {result!r} (fail_on={self.fail_on})."
            )
        self.log.info("Data quality check PASSED: result=%r", result)
        return result
