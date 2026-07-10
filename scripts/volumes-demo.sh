#!/usr/bin/env bash
# Практика «Docker Volume» — демонстрация потери данных и
# сохранения через anonymous / named / bind mount тома.
set -euo pipefail

IMAGE="luba30analyst/docker-practice-app-volume:v1"
PG="psql -U appuser -d appdb -v ON_ERROR_STOP=1"

echo "### 0. Сборка образа (если ещё не собран)"
docker build -t "$IMAGE" -f Dockerfile.volume .

echo "### 1. Список томов до начала"
docker volume ls

echo ""
echo "============================================================"
echo "### 2. ТЕРЯЕМ ДАННЫЕ: контейнер БЕЗ явного тома (anonymous)"
echo "============================================================"
docker container run -d --name pg-lost \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  "$IMAGE"

for i in $(seq 1 30); do
  docker container exec pg-lost pg_isready -U appuser -d appdb >/dev/null 2>&1 && break
  sleep 2
done

docker container exec pg-lost $PG -c "CREATE TABLE test (id serial PRIMARY KEY, note text);"
docker container exec pg-lost $PG -c "INSERT INTO test (note) VALUES ('эти данные мы сейчас потеряем');"
echo "--- данные в контейнере pg-lost:"
docker container exec pg-lost $PG -c "SELECT * FROM test;"

echo "--- anonymous volume, созданный автоматически:"
docker container inspect pg-lost -f '{{json .Mounts}}'

echo "--- удаляем контейнер pg-lost"
docker container rm -f pg-lost

docker container run -d --name pg-lost2 \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  "$IMAGE"
for i in $(seq 1 30); do
  docker container exec pg-lost2 pg_isready -U appuser -d appdb >/dev/null 2>&1 && break
  sleep 2
done
echo "--- пытаемся найти таблицу test в новом контейнере (данных НЕТ):"
docker container exec pg-lost2 $PG -c "\dt" || true
docker container exec pg-lost2 $PG -c "SELECT * FROM test;" || echo ">>> ОШИБКА: таблицы test нет — данные ПОТЕРЯНЫ (как и ожидалось)"
docker container rm -f pg-lost2 >/dev/null
echo ""
echo "============================================================"
echo "### 3. NAMED VOLUME: данные сохраняются после удаления контейнера"
echo "============================================================"
docker volume create pgdata-named
docker container run -d --name pg-named \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  -v pgdata-named:/var/lib/postgresql/data \
  "$IMAGE"
for i in $(seq 1 30); do
  docker container exec pg-named pg_isready -U appuser -d appdb >/dev/null 2>&1 && break
  sleep 2
done
docker container exec pg-named $PG -c "CREATE TABLE users (id serial PRIMARY KEY, name text, email text);"
docker container exec pg-named $PG -c "INSERT INTO users (name, email) VALUES ('Иван','иван@example.com'),('Анна','анна@example.com');"
echo "--- данные в pg-named:"
docker container exec pg-named $PG -c "SELECT * FROM users;"
echo "--- inspect named volume:"
docker volume inspect pgdata-named

echo "--- удаляем контейнер, но НЕ том"
docker container rm -f pg-named

echo "--- создаём НОВЫЙ контейнер с тем же named volume -> данные СОХРАНИЛИСЬ:"
docker container run -d --name pg-named2 \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  -v pgdata-named:/var/lib/postgresql/data \
  "$IMAGE"
for i in $(seq 1 30); do
  docker container exec pg-named2 pg_isready -U appuser -d appdb >/dev/null 2>&1 && break
  sleep 2
done
docker container exec pg-named2 $PG -c "SELECT * FROM users;"
docker container rm -f pg-named2 >/dev/null

echo ""
echo "============================================================"
echo "### 4. BIND MOUNT: данные в папке на хосте"
echo "============================================================"
HOST_DIR="$(pwd)/pgdata-bind"
mkdir -p "$HOST_DIR"
docker container run -d --name pg-bind \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  -v "$HOST_DIR":/var/lib/postgresql/data \
  "$IMAGE"
for i in $(seq 1 30); do
  docker container exec pg-bind pg_isready -U appuser -d appdb >/dev/null 2>&1 && break
  sleep 2
done
docker container exec pg-bind $PG -c "CREATE TABLE notes (id serial PRIMARY KEY, text text);"
docker container exec pg-bind $PG -c "INSERT INTO notes (text) VALUES ('сохранено через bind mount');"
echo "--- данные в pg-bind:"
docker container exec pg-bind $PG -c "SELECT * FROM notes;"
echo "--- inspect (тип mount: bind):"
docker container inspect pg-bind -f '{{json .Mounts}}'

echo "--- удаляем контейнер, данные остаются в папке хоста:"
docker container rm -f pg-bind
echo "--- файлы PostgreSQL в хост-папке $HOST_DIR :"
ls -la "$HOST_DIR" | head

echo "--- новый контейнер с тем же bind mount -> данные СОХРАНИЛИСЬ:"
docker container run -d --name pg-bind2 \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  -v "$HOST_DIR":/var/lib/postgresql/data \
  "$IMAGE"
for i in $(seq 1 30); do
  docker container exec pg-bind2 pg_isready -U appuser -d appdb >/dev/null 2>&1 && break
  sleep 2
done
docker container exec pg-bind2 $PG -c "SELECT * FROM notes;"
docker container rm -f pg-bind2 >/dev/null

echo ""
echo "============================================================"
echo "### 5. Команды работы с томами и очистка"
echo "============================================================"
docker volume ls
docker volume inspect pgdata-named
echo "--- удаляем named volume (данные удалятся):"
docker volume rm pgdata-named
echo "--- хост-папку bind mount можно удалить вручную:"
rm -rf "$HOST_DIR"
echo "--- очистка неиспользуемых томов (анонимные, оставшиеся от потерянных контейнеров):"
docker volume prune -f
echo "Готово."
