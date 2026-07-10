# docker-practice-app

Практическая работа по модулю **Docker** курса «Аналитика и инженерия данных»:
- **Docker Images** — создание своего образа, теги, публикация.
- **Dockerfile** — инструкции сборки, `.dockerignore`.
- **Docker Containers** — несколько Dockerfile (PostgreSQL + Python-клиент к БД), сборка образов, запуск контейнеров разными способами (`run`, `create + start`, `restart`), тест основных команд (`ls`, `stop`, `inspect`, `logs`, `exec`, `rm`, `prune`).

Репозиторий на GitHub: [github.com/l-uba-creator/docker-practice-app](https://github.com/l-uba-creator/docker-practice-app)

## Образы на Docker Hub (публичные)

| Образ | Назначение | Ссылка |
|---|---|---|
| `luba30analyst/docker-practice-app` | Python-приложение | [hub.docker.com/r/luba30analyst/docker-practice-app](https://hub.docker.com/r/luba30analyst/docker-practice-app) |
| `luba30analyst/docker-practice-app-db` | PostgreSQL + init-схема | [hub.docker.com/r/luba30analyst/docker-practice-app-db](https://hub.docker.com/r/luba30analyst/docker-practice-app-db) |
| `luba30analyst/docker-practice-app-client` | Python-клиент к БД | [hub.docker.com/r/luba30analyst/docker-practice-app-client](https://hub.docker.com/r/luba30analyst/docker-practice-app-client) |

Теги: `v1`, `v2` (только app), `latest`.

## Структура

```
.
├── Dockerfile                    # Образ Python-приложения
├── Dockerfile.db                 # Образ PostgreSQL + init.sql
├── Dockerfile.client             # Образ Python-клиента к БД
├── .dockerignore
├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── db_client.py
│   └── requirements-client.txt
├── db/
│   └── init.sql
├── scripts/
│   └── containers-demo.sh
├── docker-compose.yml
└── .github/workflows/docker-publish.yml
```

## Сборка образов

```bash
# 1. Основное приложение
docker build -t luba30analyst/docker-practice-app:v1 .
docker build -t luba30analyst/docker-practice-app:v2 --build-arg APP_VERSION=v2 .
docker tag luba30analyst/docker-practice-app:v2 luba30analyst/docker-practice-app:latest

# 2. PostgreSQL с init-схемой
docker build -t luba30analyst/docker-practice-app-db:v1 -f Dockerfile.db .

# 3. Python-клиент
docker build -t luba30analyst/docker-practice-app-client:v1 -f Dockerfile.client .
```

## Работа с контейнерами (Docker Containers practice)

```bash
docker network create practice-net

# Запуск через run
docker container run -d --name db --network practice-net \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  luba30analyst/docker-practice-app-db:v1

docker container run --rm --name client --network practice-net -e PG_HOST=db \
  luba30analyst/docker-practice-app-client:v1

# Запуск через create + start
docker container create --name client --network practice-net -e PG_HOST=db \
  luba30analyst/docker-practice-app-client:v1
docker container start -a client

# Основные команды
docker container ls                # запущенные
docker container ls -a             # все
docker container logs db
docker container inspect db
docker container exec db psql -U appuser -d appdb -c "SELECT count(*) FROM visits;"
docker container restart db
docker container stop db client
docker container rm db client
docker container prune -f
```

Полный протокол теста команд — в `scripts/containers-demo.sh`.

### Через docker compose

```bash
docker compose up --build
docker compose down
```

## CI/CD (GitHub Actions)

Workflow `.github/workflows/docker-publish.yml` собирает и пушит все образы при пуше в `main` или вручную (Actions → Run workflow).

Нужны секреты репозитория (Settings → Secrets and variables → Actions):
- `DOCKERHUB_USERNAME` — `luba30analyst`
- `DOCKERHUB_TOKEN` — Access Token Docker Hub

## Источники

- [Docker Containers reference — Docker Docs](https://docs.docker.com/reference/cli/docker/container/)
- [Build, tag, and publish an image — Docker Docs](https://docs.docker.com/get-started/docker-concepts/building-images/build-tag-and-publish-an-image/)
- [Dockerfile reference — Docker Docs](https://docs.docker.com/reference/dockerfile/)
- [docker image push — Docker Docs](https://docs.docker.com/reference/cli/docker/image/push/)
- [PostgreSQL image — Docker Hub](https://hub.docker.com/_/postgres)
