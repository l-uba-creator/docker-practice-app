# docker-practice-app

Практическая работа по модулю **Docker** курса «Аналитика и инженерия данных»:
- **Docker Images** — создание своего образа, теги, публикация.
- **Dockerfile** — инструкции сборки, `.dockerignore`.
- **Docker Containers** — несколько Dockerfile (PostgreSQL + Python-клиент к БД), сборка образов, запуск контейнеров разными способами (`run`, `create + start`, `restart`), тест основных команд (`ls`, `stop`, `inspect`, `logs`, `exec`, `rm`, `prune`).
- **Docker Networks** — связывание контейнеров через сети; создание сетей `bridge`/`host`/`none`, `inspect`, `connect`/`disconnect`, ping по IP и по имени контейнера, образ `nicolaka/netshoot`, связка Python ↔ PostgreSQL по имени хоста.

Репозиторий на GitHub: [github.com/l-uba-creator/docker-practice-app](https://github.com/l-uba-creator/docker-practice-app)

## Образы на Docker Hub (публичные)

| Образ | Назначение | Ссылка |
|---|---|---|
| `luba30analyst/docker-practice-app` | Python-приложение | [hub.docker.com/r/luba30analyst/docker-practice-app](https://hub.docker.com/r/luba30analyst/docker-practice-app) |
| `luba30analyst/docker-practice-app-db` | PostgreSQL + init-схема | [hub.docker.com/r/luba30analyst/docker-practice-app-db](https://hub.docker.com/r/luba30analyst/docker-practice-app-db) |
| `luba30analyst/docker-practice-app-client` | Python-клиент к БД | [hub.docker.com/r/luba30analyst/docker-practice-app-client](https://hub.docker.com/r/luba30analyst/docker-practice-app-client) |
| `luba30analyst/docker-practice-app-users` | Python-клиент: таблица Users (Docker Networks practice) | [hub.docker.com/r/luba30analyst/docker-practice-app-users](https://hub.docker.com/r/luba30analyst/docker-practice-app-users) |

Теги: `v1`, `v2` (только app), `latest`.

## Структура

```
.
├── Dockerfile                    # Образ Python-приложения
├── Dockerfile.db                 # Образ PostgreSQL + init.sql
├── Dockerfile.client             # Образ Python-клиента к БД
├── Dockerfile.users              # Образ Python-клиента с таблицей Users (Networks practice)
├── .dockerignore
├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── db_client.py
│   ├── users_client.py
│   └── requirements-client.txt
├── db/
│   └── init.sql
├── scripts/
│   ├── containers-demo.sh
│   └── networks-demo.sh
├── docker-compose.yml
├── docker-compose-networks.yml
└── .github/workflows/docker-publish.yml
```

## Docker Networks (практика)

Типы сетей: `bridge` (default, пользовательная — с DNS-резолвингом имён), `host` (сетевой стек хоста), `none` (без сети).

```bash
docker network ls
docker network create --driver bridge my-bridge-net
docker network create --driver host   my-host-net
docker network create --driver null   my-none-net
docker network inspect my-bridge-net
docker network connect    my-bridge-net <container>
docker network disconnect my-bridge-net <container>
```

### Тестирование связности через nicolaka/netshoot

```bash
docker pull nicolaka/netshoot
docker run -d --name net1 nicolaka/netshoot sleep infinity
docker run -d --name net2 nicolaka/netshoot sleep infinity
NET2_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' net2)
docker exec net1 ping -c 3 "$NET2_IP"
# В пользовательской bridge-сети DNS-резолвинг имён работает:
docker run -d --name nb1 --network my-bridge-net nicolaka/netshoot sleep infinity
docker run -d --name nb2 --network my-bridge-net nicolaka/netshoot sleep infinity
docker exec nb1 ping -c 3 nb2
```

### Связка Python ↔ PostgreSQL по имени хоста через docker-сеть

```bash
docker run -d --name db --network my-bridge-net \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  luba30analyst/docker-practice-app-db:v1

docker run --rm --name users --network my-bridge-net \
  -e PG_HOST=db \
  luba30analyst/docker-practice-app-users:v1
```

Полный протокол теста команд сетей — в `scripts/networks-demo.sh`.

## CI/CD (GitHub Actions)

Workflow `.github/workflows/docker-publish.yml` собирает и пушит все образы при пуше в `main` или вручную (Actions → Run workflow).

Нужны секреты репозитория (Settings → Secrets and variables → Actions):
- `DOCKERHUB_USERNAME` — `luba30analyst`
- `DOCKERHUB_WRITE_TOKEN` — Access Token Docker Hub (Read & Write)

## Источники

- [Docker Networks reference — Docker Docs](https://docs.docker.com/reference/cli/docker/network/)
- [Docker Containers reference — Docker Docs](https://docs.docker.com/reference/cli/docker/container/)
- [Dockerfile reference — Docker Docs](https://docs.docker.com/reference/dockerfile/)
- [docker image push — Docker Docs](https://docs.docker.com/reference/cli/docker/image/push/)
- [PostgreSQL image — Docker Hub](https://hub.docker.com/_/postgres)
- [nicolaka/netshoot — Docker Hub](https://hub.docker.com/r/nicolaka/netshoot)
