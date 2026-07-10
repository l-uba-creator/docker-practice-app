"""
Оператор выгрузки таблицы PostgreSQL в объектное хранилище (S3/MinIO) в CSV.

Использует:
  - PostgresHook + COPY ... TO STDOUT WITH CSV HEADER для формирования CSV;
  - S3Hook (Amazon provider) для загрузки файла в бакет.

Ключ в хранилище формируется как:
    <s3_key_prefix>/<table_name>/<ds>.csv
что обеспечивает версионирование по логическому дню выполнения DAG.

Создаётся ТОЛЬКО для таблиц, у которых в конфиге `need_to_export = True`
(см. логику генерации DAG в dynamic_etl_dag.py).

Документация:
- https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/_api/airflow/providers/amazon/hooks/s3/index.html
- https://www.postgresql.org/docs/current/sql-copy.html
"""

from __future__ import annotations

import io

from airflow.models import BaseOperator
from airflow.providers.amazon.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook


class PostgresToS3CSVOperator(BaseOperator):
    """Выгружает таблицу в CSV и кладёт в объектное хранилище S3."""

    template_fields = ("ds", "s3_key")

    def __init__(
        self,
        postgres_conn_id: str,
        aws_conn_id: str,
        table_name: str,
        s3_bucket: str,
        s3_key_prefix: str,
        ds: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.postgres_conn_id = postgres_conn_id
        self.aws_conn_id = aws_conn_id
        self.table_name = table_name
        self.s3_bucket = s3_bucket
        self.s3_key_prefix = s3_key_prefix
        self.ds = ds
        self.s3_key = f"{s3_key_prefix}/{table_name}/{ds}.csv"

    def execute(self, context) -> str:
        pg = PostgresHook(postgres_conn_id=self.postgres_conn_id)

        # COPY ... TO STDOUT формирует CSV прямо на стороне БД — без
        # материализации полной таблицы в памяти воркера (стримится по строкам).
        buffer = io.StringIO()
        pg.copy_expert(
            sql=(
                f"COPY (SELECT * FROM {self.table_name}) "
                "TO STDOUT WITH CSV HEADER"
            ),
            filename=buffer,
        )
        csv_bytes = buffer.getvalue().encode("utf-8")
        self.log.info(
            "Prepared CSV for %s: %d bytes", self.table_name, len(csv_bytes)
        )

        s3 = S3Hook(aws_conn_id=self.aws_conn_id)
        s3.load_bytes(
            bytes_data=csv_bytes,
            key=self.s3_key,
            bucket_name=self.s3_bucket,
            replace=True,
        )
        self.log.info(
            "Exported %s -> s3://%s/%s",
            self.table_name,
            self.s3_bucket,
            self.s3_key,
        )
        return f"s3://{self.s3_bucket}/{self.s3_key}"
