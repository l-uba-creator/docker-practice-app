#!/usr/bin/bash
# Создаёт Airflow Connections, необходимые для работы DAG.
# Запускать внутри контейнера scheduler:
#   docker compose exec airflow-scheduler bash /opt/airflow/scripts/setup_connections.sh
set -euo pipefail

airflow connections delete pg_warehouse || true
airflow connections add pg_warehouse \
    --conn-uri "postgres://airflow:airflow@postgres:5432/warehouse"

airflow connections delete s3_minio || true
airflow connections add s3_minio \
    --conn-type aws \
    --conn-extra '{"endpoint_url":"http://minio:9000","region_name":"us-east-1"}'

echo "Connections ready:"
airflow connections list | grep -E "pg_warehouse|s3_minio"
