# docker-practice-app

Docker-образ для практики Docker Images (курс «Аналитика и инженерия данных», модуль Docker).

## Репозиторий на Docker Hub

Образ публикуется автоматически через GitHub Actions:
**https://hub.docker.com/r/luba30analyst/docker-practice-app**

Теги:
- `v1` — первая версия образа
- `v2` — обновлённая версия (через `--build-arg APP_VERSION=v2`)
- `latest` — указатель на v2

## Использование

```bash
# Запуск версии v1
docker run --rm luba30analyst/docker-practice-app:v1

# Запуск версии v2 / latest
docker run --rm luba30analyst/docker-practice-app:v2
```

## Сборка локально

```bash
docker build -t luba30analyst/docker-practice-app:v1 .
docker build -t luba30analyst/docker-practice-app:v2 --build-arg APP_VERSION=v2 .
docker tag luba30analyst/docker-practice-app:v2 luba30analyst/docker-practice-app:latest
```

## CI/CD (GitHub Actions)

Workflow `.github/workflows/docker-publish.yml` собирает и пушит образ при пуше в `main` или вручную (вкладка Actions → Run workflow).

Нужны секреты репозитория (Settings → Secrets and variables → Actions):
- `DOCKERHUB_USERNAME` — `luba30analyst`
- `DOCKERHUB_TOKEN` — ваш API-токен Docker Hub

## Структура

```
.
├── Dockerfile                       # Инструкции сборки (FROM, WORKDIR, COPY, ARG, CMD)
├── .dockerignore                    # Исключения из build context
├── app/
│   ├── main.py                      # Python-приложение: вывод версии/платформы
│   └── requirements.txt            # Зависимости (пустой — для демонстрации слоёв)
└── .github/workflows/
    └── docker-publish.yml           # GitHub Actions: build & push to Docker Hub
```

## Описание файлов

| Файл | Назначение |
|---|---|
| `Dockerfile` | Инструкции сборки образа: базовый образ `python:3.12-slim`, LABEL (метаданные), WORKDIR `/app`, COPY requirements.txt + pip install, COPY app/, ARG `APP_VERSION`, ENV, CMD `python main.py` |
| `.dockerignore` | Файлы, исключаемые из build context (`.git/`, `*.md`, `__pycache__/` и т.д.) — ускоряет сборку и уменьшает размер образа |
| `app/main.py` | Python-приложение: выводит версию приложения, версию Python, платформу и hostname. Версия берётся из переменной окружения `APP_VERSION` (по умолчанию `v1`) |
| `app/requirements.txt` | Зависимости приложения (пустой — демонстрирует кэширование слоёв при изменении зависимостей) |
| `.github/workflows/docker-publish.yml` | GitHub Actions workflow: вход в Docker Hub, сборка и пуш тегов `v1`, `v2`, `latest` |

## Версионирование

Образ использует систему тегов для версионирования:
- `APP_VERSION` передаётся через `--build-arg` при сборке
- Разные теги (`v1`, `v2`) хранят разные версии в одном репозитории
- `latest` указывает на последнюю стабильную версию (`v2`)

## Источники
- [Build, tag, and publish an image — Docker Docs](https://docs.docker.com/get-started/docker-concepts/building-images/build-tag-and-publish-an-image/)
- [Dockerfile reference — Docker Docs](https://docs.docker.com/reference/dockerfile/)
- [docker image tag — Docker Docs](https://docs.docker.com/reference/cli/docker/image/tag/)
- [docker image push — Docker Docs](https://docs.docker.com/reference/cli/docker/image/push/)
