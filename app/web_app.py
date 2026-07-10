"""
Веб-приложение (Flask) для финальной практики Docker Compose.
Подключается к контейнеру PostgreSQL по имени хоста (через изолированную
docker-сеть), создаёт таблицу users, заполняет её тестовыми данными
и отдаёт HTML-страницу со списком пользователей.
"""
import os
import time
import platform

import psycopg2
from flask import Flask, jsonify

APP_VERSION = os.environ.get("APP_VERSION", "v1")

TEST_USERS = [
    ("Иванов Иван", "ivan@example.com", 28),
    ("Петрова Анна", "anna@example.com", 34),
    ("Сидоров Пётр", "petr@example.com", 41),
    ("Кузнецова Мария", "maria@example.com", 23),
    ("Смирнов Алексей", "alex@example.com", 37),
]

app = Flask(__name__)


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("PG_HOST", "db"),
        port=int(os.environ.get("PG_PORT", "5432")),
        user=os.environ.get("PG_USER", "appuser"),
        password=os.environ.get("PG_PASSWORD", "apppass"),
        dbname=os.environ.get("PG_DB", "appdb"),
    )


def wait_for_db(attempts=30, delay=2):
    for i in range(1, attempts + 1):
        try:
            return get_conn()
        except psycopg2.OperationalError:
            print(f"[{i}/{attempts}] Ожидание БД...", flush=True)
            time.sleep(delay)
    raise RuntimeError("Не удалось подключиться к БД")


def init_db():
    conn = wait_for_db()
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
                    VALUES (%s, %s, %s) ON CONFLICT (email) DO NOTHING
                    """,
                    (full_name, email, age),
                )
        conn.commit()
    finally:
        conn.close()
    print("БД инициализирована: таблица users готова.", flush=True)


def fetch_users():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, full_name, email, age, created_at FROM users ORDER BY id")
            return cur.fetchall()
    finally:
        conn.close()


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Docker Compose Practice — Users</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; background:#f4f6f8; }}
  h1 {{ color:#0d3b66; }}
  table {{ border-collapse: collapse; width: 100%; background:#fff; box-shadow:0 1px 3px rgba(0,0,0,.1); }}
  th, td {{ border:1px solid #e0e0e0; padding:10px 14px; text-align:left; }}
  th {{ background:#0d3b66; color:#fff; }}
  tr:nth-child(even) {{ background:#f9fbfd; }}
  .meta {{ color:#666; font-size:.9rem; margin-top:1rem; }}
</style>
</head>
<body>
<h1>Пользователи (таблица users)</h1>
<p>Данные получены из контейнера PostgreSQL и отданы через Nginx → Flask.</p>
<table>
<tr><th>id</th><th>ФИО</th><th>Email</th><th>Возраст</th><th>Создан</th></tr>
{rows}
</table>
<p class="meta">App version: {ver} · Python · host: {host}</p>
</body>
</html>"""


@app.route("/")
def index():
    rows = fetch_users()
    body = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td></tr>"
        for r in rows
    )
    return HTML_TEMPLATE.format(rows=body, ver=APP_VERSION, host=platform.node())


@app.route("/health")
def health():
    return jsonify(status="ok", version=APP_VERSION, host=platform.node())


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
