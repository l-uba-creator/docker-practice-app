"""Точка входа плагина: регистрирует кастомные операторы в Airflow."""

from airflow.plugins_manager import AirflowPlugin

from .create_table_operator import PostgresCreateTableOperator
from .data_quality_operator import PostgresDataQualityOperator
from .export_to_s3_operator import PostgresToS3CSVOperator
from .load_table_operator import PostgresLoadTableOperator


class DynamicEtlPlugin(AirflowPlugin):
    name = "dynamic_etl_plugin"
    operators = [
        PostgresCreateTableOperator,
        PostgresLoadTableOperator,
        PostgresDataQualityOperator,
        PostgresToS3CSVOperator,
    ]
