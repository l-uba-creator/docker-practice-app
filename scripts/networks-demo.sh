#!/usr/bin/env bash
# Практика «Docker Networks» — демонстрация основных команд
# для работы с сетями и тестирования связности контейнеров.
set -euo pipefail

IMAGE_DB="luba30analyst/docker-practice-app-db:v1"
IMAGE_USERS="luba30analyst/docker-practice-app-users:v1"
NETSHOOT="nicolaka/netshoot"

echo "### 1. Список доступных сетей (по умолчанию: bridge, host, none)"
docker network ls

echo "### 2. Создание собственных сетей разных типов"
docker network create --driver bridge my-bridge-net
docker network create --driver host my-host-net
docker network create --driver null my-none-net

echo "### 3. Скачивание образа nicolaka/netshoot для тестирования сетей"
docker pull "$NETSHOOT"

echo "### 4. Два тестовых контейнера netshoot в default-сети (bridge)"
docker container run -d --name net1 "$NETSHOOT" sleep infinity
docker container run -d --name net2 "$NETSHOOT" sleep infinity

echo "### 5. Пинг из net1 -> net2 по IP-адресу"
NET2_IP=$(docker container inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' net2)
echo "IP net2 = $NET2_IP"
docker container exec net1 ping -c 3 "$NET2_IP"

echo "### 6. Пинг из net1 -> net2 по ИМЕНИ контейнера"
docker container exec net1 ping -c 3 net2 || echo "(в default bridge DNS-резолвинг имён ограничен)"

echo "### 7. inspect сети и контейнеров — проверка принадлежности сети"
docker network inspect bridge
docker container inspect net1

echo "### 8. Запуск контейнеров в различных сетях"
docker container run -d --name nb1 --network my-bridge-net "$NETSHOOT" sleep infinity
docker container run -d --name nb2 --network my-bridge-net "$NETSHOOT" sleep infinity

echo "### 9. Пинг по имени контейнера внутри пользовательской bridge-сети"
docker container exec nb1 ping -c 3 nb2

echo "### 10. Запуск контейнеров в сетях host и none"
docker container run --rm --network host --name nh "$NETSHOOT" ip addr || true
docker container run --rm --network none --name nn "$NETSHOOT" ip addr || true

echo "### 11. Подключение контейнера к сети / отключение / несколько сетей"
docker container run -d --network none --name solo "$NETSHOOT" sleep infinity
docker network connect my-bridge-net solo
docker container inspect solo -f '{{json .NetworkSettings.Networks}}'

echo "### 12. Перевод контейнера из одной сети в другую (disconnect -> connect)"
docker network disconnect none solo || true
docker network disconnect my-bridge-net solo || true
docker network connect bridge solo
docker container inspect solo -f '{{json .NetworkSettings.Networks}}'

echo "### 13. Теперь связываем Python + PostgreSQL через docker-сеть"
docker container run -d --name db --network my-bridge-net \
  -e POSTGRES_USER=appuser -e POSTGRES_PASSWORD=apppass -e POSTGRES_DB=appdb \
  "$IMAGE_DB"

echo "Ожидание готовности PostgreSQL..."
for i in $(seq 1 30); do
  docker container exec db pg_isready -U appuser -d appdb >/dev/null 2>&1 && break
  sleep 2
done

docker container run --rm --name users --network my-bridge-net \
  -e PG_HOST=db \
  "$IMAGE_USERS"

echo "### 14. Финальная очистка контейнеров и сетей"
docker container rm -f net1 net2 nb1 nb2 solo db 2>/dev/null || true
docker network rm my-bridge-net my-host-net my-none-net 2>/dev/null || true
docker network prune -f
