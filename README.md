# docker-practice-app

Практическая работа по модулю **Docker** курса «Аналитика и инженерия данных»:
- **Docker Images** — создание своего образа, теги, публикация.
- **Dockerfile** — инструкции сборки, `.dockerignore`.
- **Docker Containers** — несколько Dockerfile (PostgreSQL + Python-клиент к БД), сборка образов, запуск контейнеров разными способами (`run`, `create + start`, `restart`), тест основных команд (`ls`, `stop`, `inspect`, `logs`, `exec`, `rm`, `prune`).
- **Docker Networks** — связывание контейнеров через сети; создание сетей `bridge`/`host`/`none`, `inspect`, `connect`/`disconnect`, ping по IP и по имени контейнера, образ `nicolaka/netshoot`, связка Python ↔ PostgreSQL по имени хоста.
- **Docker Volume** — сохранение данных между запусками контейнера; демонстрация потери данных и хранение через anonymous / named volume / bind mount.

Репозиторий на GitHub: [github.com/l-uba-creator/docker-practice-app](https://github.com/l-uba-creator/docker-practice-app)

## Образы на Docker Hub (публичные)

| Образ | Назначение | Ссылка |
|---|---|---|
| `luba30analyst/docker-practice-app` | Python-приложение | [hub.docker.com/r/luba30analyst/docker-practice-app](https://hub.docker.com/r/luba30analyst/docker-practice-app) |
| `luba30analyst/docker-practice-app-db` | PostgreSQL + init-схема | [hub.docker.com/r/luba30analyst/docker-practice-app-db](https://hub.docker.com/r/luba30analyst/docker-practice-app-db) |
| `luba30analyst/docker-practice-app-client` | Python-клиент к БД | [hub.docker.com/r/luba30analyst/docker-practice-app-client](https://hub.docker.com/r/luba30analyst/docker-practice-app-client) |
| `luba30analyst/docker-practice-app-users` | Python-клиент: таблица Users (Docker Networks practice) | [hub.docker.com/r/luba30analyst/docker-practice-app-users](https://hub.docker.com/r/luba30analyst/docker-practice-app-users) |
| `luba30analyst/docker-practice-app-volume` | PostgreSQL для практики томов (Docker Volume practice) | [hub.docker.com/r/luba30analyst/docker-practice-app-volume](https://hub.docker.com/r/luba30analyst/docker-practice-app-volume) |

Теги: `v1`, `v2` (только app), `latest`.
## Docker Volume (практика)

Данные внутри контейнера теряются при его удалении. Тома Docker (`volumes`) решают эту проблему.

Типы томов:
- **Anonymous volume** — том без имени, создаётся автоматически (например, объявленный `VOLUME` в образе); привязан к контейнеру, теряется при очистке.
- **Named volume** — именованный том в docker area (`/var/lib/docker/volumes/`); сохраняется после удаления контейнера.
- **Bind mount** — монтирование папки хоста в контейнер (`-v /host/path:/container/path`); данные лежат на хосте.

```bash
docker volume create pgdata-named
docker volume ls
docker volume inspect pgdata-named
docker volume rm pgdata-named
docker volume prune -f
```

### Демонстрация потери данных (контейнер без именованного тома)

```bash
docker run -d --name pg-lost \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  luba30analyst/docker-practice-app-volume:v1
docker exec pg-lost psql -U appuser -d appdb -c "CREATE TABLE test (id serial PRIMARY KEY, note text);"
docker exec pg-lost psql -U appuser -d appdb -c "INSERT INTO test (note) VALUES ('потеряем');"
docker rm -f pg-lost
docker run -d --name pg-lost2 -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  luba30analyst/docker-practice-app-volume:v1
docker exec pg-lost2 psql -U appuser -d appdb -c "SELECT * FROM test;"  # ошибка — таблицы нет
```

### Named volume — данные сохраняются

```bash
docker volume create pgdata-named
docker run -d --name pg-named \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  -v pgdata-named:/var/lib/postgresql/data \
  luba30analyst/docker-practice-app-volume:v1
docker exec pg-named psql -U appuser -d appdb -c "CREATE TABLE users (id serial PRIMARY KEY, name text); INSERT INTO users (name) VALUES ('Иван');"
docker rm -f pg-named
docker run -d --name pg-named2 \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  -v pgdata-named:/var/lib/postgresql/data \
  luba30analyst/docker-practice-app-volume:v1
docker exec pg-named2 psql -U appuser -d appdb -c "SELECT * FROM users;"
```

### Bind mount — данные в папке хоста

```bash
mkdir -p ./pgdata-bind
docker run -d --name pg-bind \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  -v ./pgdata-bind:/var/lib/postgresql/data \
  luba30analyst/docker-practice-app-volume:v1
docker exec pg-bind psql -U appuser -d appdb -c "CREATE TABLE notes (id serial PRIMARY KEY, t text); INSERT INTO notes (t) VALUES ('bind mount');"
docker rm -f pg-bind
ls ./pgdata-bind
```

Полный протокол (потеря данных + named + bind mount + очистка) — в `scripts/volumes-demo.sh`.

### Через docker compose (с именованным томом)

```bash
docker compose -f docker-compose-volume.yml up
docker compose -f docker-compose-volume.yml down
```

## CI/CD (GitHub Actions)

Workflow `.github/workflows/docker-publish.yml` собирает и пушит все образы при пуше в `main` или вручную (Actions → Run workflow).

Нужны секреты репозитория (Settings → Secrets and variables → Actions):
- `DOCKERHUB_USERNAME` — `luba30analyst`
- `DOCKERHUB_WRITE_TOKEN` — Access Token Docker Hub (Read & Write)

## Источники

- [Docker Volumes reference — Docker Docs](https://docs.docker.com/reference/cli/docker/volume/)
- [Docker Networks reference — Docker Docs](https://docs.docker.com/reference/cli/docker/network/)
- [Docker Containers reference — Docker Docs](https://docs.docker.com/reference/cli/docker/container/)
- [Dockerfile reference — Docker Docs](https://docs.docker.com/reference/dockerfile/)
- [docker image push — Docker Docs](https://docs.docker.com/reference/cli/docker/image/push/)
- [PostgreSQL image — Docker Hub](https://hub.docker.com/_/postgres)
- [nicolaka/netshoot — Docker Hub](https://hub.docker.com/r/nicolaka/netshoot)
