# syntax=docker/dockerfile:1
FROM python:3.12-slim
LABEL org.opencontainers.image.title="docker-practice-app"
LABEL org.opencontainers.image.description="Practice image for Docker Images lesson"
LABEL org.opencontainers.image.source="https://hub.docker.com/r/luba30analyst/docker-practice-app"
WORKDIR /app
COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./
ARG APP_VERSION=v1
ENV APP_VERSION=${APP_VERSION}
CMD ["python", "main.py"]
