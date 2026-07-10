"""
Python-клиент к PostgreSQL-контейнеру для практики «Docker Networks».
Подключается к БД, создаёт таблицу Users, заполняет её тестовыми
данными и выводит результат простым SELECT.

Параметры подключения берутся из переменных окружения — так контейнеры
связываются через docker-сеть по имени хоста (имени контейнера).
"""
import os
import sys
import time
import platform

import psycopg2

APP_VERSION = os.environ.get("APP_VERSION", "v1")

TEST_USERS = [
    ("Иванов Иван", "ivan@example.com", 28),
    ("Петрова Анна", "anna@example.com", 34),
    ("Сидоров Пётр", "petr@example.com", 41),
    ("Кузнецова Мария", "maria@example.com", 23),
    ("Смирнов Алексей", "alex@example.com", 37),
]


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
            return psycopg2.connect(**params)
        except psycopg2.OperationalError:
            print(f"[{i}/{attempts}] Ожидание БД {params['host']}:{params['port']}...")
            time.sleep(delay)
    raise RuntimeError("Не удалось подключиться к БД за отведённое число попыток")


def main():
    print("=" * 55)
    print("  Docker Networks Practice — Python ↔ PostgreSQL")
    print("=" * 55)
    print(f"App version:  {APP_VERSION}")
    print(f"Python:       {sys.version.split()[0]}")
    print(f"Platform:     {platform.system()} {platform.machine()}")
    print(f"Hostname:     {platform.node()}")
    params = get_connection_params()
    print(f"DB host:      {params['host']}:{params['port']}/{params['dbname']}")
    print("=" * 55)

    conn = wait_for_db(params)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(120) NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    age INTEGER,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )

            for full_name, email, age in TEST_USERS:
                cur.execute(
                    """
                    INSERT INTO users (full_name, email, age)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                    """,
                    (full_name, email, age),
                )
            conn.commit()

            cur.execute("SELECT id, full_name, email, age FROM users ORDER BY id")
            rows = cur.fetchall()
            print(f"SELECT вернул {len(rows)} записей из таблицы users:")
            print("-" * 55)
            print(f"{'id':>3}  {'full_name':<20} {'email':<22} {'age':>3}")
            print("-" * 55)
            for r in rows:
                print(f"{r[0]:>3}  {r[1]:<20} {r[2]:<22} {r[3]:>3}")
            print("-" * 55)

            cur.execute("SELECT count(*) FROM users")
            print(f"Всего пользователей: {cur.fetchone()[0]}")
        conn.commit()
    finally:
        conn.close()

    print("=" * 55)
    print("Python-контейнер успешно подключился к PostgreSQL-контейнеру")
    print("по имени хоста через docker-сеть.")
    print("=" * 55)


if __name__ == "__main__":
    main()
