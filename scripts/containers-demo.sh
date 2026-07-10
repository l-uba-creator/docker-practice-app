#!/usr/bin/env bash
# Практика «Докер Containers» — демонстрация основных команд.
set -euo pipefail

IMAGE_DB="luba30analyst/docker-practice-app-db:v1"
IMAGE_CLIENT="luba30analyst/docker-practice-app-client:v1"

echo "### 1. Список образов"
docker image ls

echo "### 2. Создание и запуск контейнера БД через run"
docker container run -d --name practice-db -p 5432:5432 "$IMAGE_DB"

echo "### 3. Создание контейнера-клиента через create"
docker container create --name practice-client -e PG_HOST=practice-db "$IMAGE_CLIENT"

echo "### 4. Запуск созданного контейнера через start"
docker container start practice-client

echo "### 5. Список контейнеров"
docker container ls
docker container ls -a

echo "### 6. Логи контейнеров"
docker container logs practice-db
docker container logs practice-client

echo "### 7. Подробная информация о контейнере (inspect)"
docker container inspect practice-client

echo "### 8. Выполнение команды внутри контейнера (exec)"
docker container exec practice-db psql -U appuser -d appdb -c "SELECT count(*) FROM visits;"

echo "### 9. Перезапуск контейнера (restart)"
docker container restart practice-client
docker container logs --tail 5 practice-client

echo "### 10. Остановка контейнеров (stop)"
docker container stop practice-db practice-client

echo "### 11. Удаление контейнеров (rm)"
docker container rm practice-db practice-client

echo "### 12. Полная очистка (prune)"
docker container prune -f
