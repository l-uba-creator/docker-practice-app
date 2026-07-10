# docker-practice-app

Практическая работа по модулю **Docker** курса «Аналитика и инженерия данных»:
- **Docker Images** — создание своего образа, теги, публикация.
- **Dockerfile** — инструкции сборки, `.dockerignore`.
- **Docker Containers** — несколько Dockerfile (PostgreSQL + Python-клиент к БД), сборка образов, запуск контейнеров разными способами (`run`, `create + start`, `restart`), тест основных команд (`ls`, `stop`, `inspect`, `logs`, `exec`, `rm`, `prune`).
- **Docker Networks** — связывание контейнеров через сети; создание сетей `bridge`/`host`/`none`, `inspect`, `connect`/`disconnect`, ping по IP и по имени контейнера, образ `nicolaka/netshoot`, связка Python ↔ PostgreSQL по имени хоста.
- **Docker Volume** — сохранение данных между запусками контейнера; демонстрация потери данных и хранение через anonymous / named volume / bind mount.
- **Docker Compose** — многоконтейнерное приложение (PostgreSQL + Flask + Nginx) в одном YAML: собственная сеть, named volume, reverse proxy.

Репозиторий на GitHub: [github.com/l-uba-creator/docker-practice-app](https://github.com/l-uba-creator/docker-practice-app)

## Образы на Docker Hub (публичные)

| Образ | Назначение | Ссылка |
|---|---|---|
| `luba30analyst/docker-practice-app` | Python-приложение | [hub.docker.com/r/luba30analyst/docker-practice-app](https://hub.docker.com/r/luba30analyst/docker-practice-app) |
| `luba30analyst/docker-practice-app-db` | PostgreSQL + init-схема | [hub.docker.com/r/luba30analyst/docker-practice-app-db](https://hub.docker.com/r/luba30analyst/docker-practice-app-db) |
| `luba30analyst/docker-practice-app-client` | Python-клиент к БД | [hub.docker.com/r/luba30analyst/docker-practice-app-client](https://hub.docker.com/r/luba30analyst/docker-practice-app-client) |
| `luba30analyst/docker-practice-app-users` | Python-клиент: таблица Users (Docker Networks practice) | [hub.docker.com/r/luba30analyst/docker-practice-app-users](https://hub.docker.com/r/luba30analyst/docker-practice-app-users) |
| `luba30analyst/docker-practice-app-volume` | PostgreSQL для практики томов (Docker Volume practice) | [hub.docker.com/r/luba30analyst/docker-practice-app-volume](https://hub.docker.com/r/luba30analyst/docker-practice-app-volume) |
| `luba30analyst/docker-practice-app-web` | Flask: данные из БД в веб (Docker Compose practice) | [hub.docker.com/r/luba30analyst/docker-practice-app-web](https://hub.docker.com/r/luba30analyst/docker-practice-app-web) |
| `luba30analyst/docker-practice-app-nginx` | Nginx reverse proxy (Docker Compose practice) | [hub.docker.com/r/luba30analyst/docker-practice-app-nginx](https://hub.docker.com/r/luba30analyst/docker-practice-app-nginx) |

Теги: `v1`, `v2` (только app), `latest`.

## Docker Compose (финальная практика)

Многоконтейнерное приложение в одном YAML: PostgreSQL + Flask + Nginx.
Все контейнеры работают в собственной изолированной сети `compose-appnet`,
данные PostgreSQL хранятся в named volume `compose-pgdata`.

```bash
docker compose -f docker-compose-final.yml up --build
# открыть в браузере: http://localhost:8080
docker compose -f docker-compose-final.yml ps
docker compose -f docker-compose-final.yml logs
docker compose -f docker-compose-final.yml exec db psql -U appuser -d appdb -c "SELECT * FROM users;"
docker compose -f docker-compose-final.yml down
```

Архитектура: `http://localhost:8080` → Nginx (reverse proxy) → Flask `web:8080` → PostgreSQL `db`.
Flask при старте создаёт таблицу `users` и заполняет её тестовыми данными, затем отдаёт HTML-страницу со списком пользователей.

## CI/CD (GitHub Actions)

Workflow `.github/workflows/docker-publish.yml` собирает и пушит все образы при пуше в `main` или вручную (Actions → Run workflow).

Нужны секреты репозитория (Settings → Secrets and variables → Actions):
- `DOCKERHUB_USERNAME` — `luba30analyst`
- `DOCKERHUB_WRITE_TOKEN` — Access Token Docker Hub (Read & Write)

## Источники

- [Docker Compose reference — Docker Docs](https://docs.docker.com/reference/cli/docker/compose/)
- [Compose file reference — Docker Docs](https://docs.docker.com/compose/compose-file/)
- [Docker Volumes reference — Docker Docs](https://docs.docker.com/reference/cli/docker/volume/)
- [Docker Networks reference — Docker Docs](https://docs.docker.com/reference/cli/docker/network/)
- [Docker Containers reference — Docker Docs](https://docs.docker.com/reference/cli/docker/container/)
- [Dockerfile reference — Docker Docs](https://docs.docker.com/reference/dockerfile/)
- [docker image push — Docker Docs](https://docs.docker.com/reference/cli/docker/image/push/)
- [PostgreSQL image — Docker Hub](https://hub.docker.com/_/postgres)
- [nicolaka/netshoot — Docker Hub](https://hub.docker.com/r/nicolaka/netshoot)
