"""
Python-клиент к PostgreSQL-контейнеру.
Демонстрирует взаимодействие контейнеров: подключение к БД,
создание таблицы, вставка и чтение данных.
"""
import os
import sys
import time
import platform

import psycopg2

APP_VERSION = os.environ.get("APP_VERSION", "v1")


def get_connection_params():
    return {
        "host": os.environ.get("PG_HOST", "db"),
        "port": int(os.environ.get("PG_PORT", "5432")),
        "user": os.environ.get("PG_USER", "appuser"),
        "password": os.environ.get("PG_PASSWORD", "apppass"),
        "dbname": os.environ.get("PG_DB", "appdb"),
    }


def wait_for_db(params, attempts=30, delay=2):
    for i in range(1, attempts + 1):
        try:
            conn = psycopg2.connect(**params)
            return conn
        except psycopg2.OperationalError:
            print(f"[{i}/{attempts}] Ожидание БД {params['host']}:{params['port']}...")
            time.sleep(delay)
    raise RuntimeError("Не удалось подключиться к БД за отведённое число попыток")


def main():
    print("=" * 50)
    print("  Docker Containers Practice — Python DB Client")
    print("=" * 50)
    print(f"App version:  {APP_VERSION}")
    print(f"Python:       {sys.version.split()[0]}")
    print(f"Platform:     {platform.system()} {platform.machine()}")
    print(f"Hostname:     {platform.node()}")
    params = get_connection_params()
    print(f"DB host:      {params['host']}:{params['port']}/{params['dbname']}")
    print("=" * 50)

    conn = wait_for_db(params)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS visits (
                    id SERIAL PRIMARY KEY,
                    message TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
            cur.execute(
                "INSERT INTO visits (message) VALUES (%s) RETURNING id, message, created_at",
                (f"Hello from container {platform.node()}",),
            )
            row = cur.fetchone()
            print(f"Вставлена запись: id={row[0]}, message='{row[1]}', at={row[2]}")

            cur.execute("SELECT count(*) FROM visits")
            count = cur.fetchone()[0]
            print(f"Всего записей в таблице visits: {count}")

            cur.execute("SELECT id, message, created_at FROM visits ORDER BY id DESC LIMIT 5")
            print("Последние 5 записей:")
            for r in cur.fetchall():
                print(f"  #{r[0]}  {r[1]}  ({r[2]})")
        conn.commit()
    finally:
        conn.close()

    print("=" * 50)
    print("Контейнер-клиент успешно подключился к контейнеру с БД.")
    print("=" * 50)


if __name__ == "__main__":
    main()
