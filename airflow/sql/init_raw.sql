-- Сырые источники (raw-слой) для демонстрации работы динамического DAG.
-- Файл монтируется в init-скрипт PostgreSQL контейнера и выполняется при первом старте.

-- Таблица сырых платежей
CREATE TABLE IF NOT EXISTS raw_payments (
    id          bigserial PRIMARY KEY,
    category    varchar(64) NOT NULL,
    amount      numeric(18,2) NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Таблица сырых пользователей
CREATE TABLE IF NOT EXISTS raw_users (
    id          bigserial PRIMARY KEY,
    category    varchar(64) NOT NULL,
    balance     numeric(18,2) NOT NULL DEFAULT 0
);

-- Демо-данные. Генерируем через generate_series, чтобы при каждом запуске
-- (для даты ds = сегодня) были свежие строки.
INSERT INTO raw_payments (category, amount, created_at)
SELECT
    (ARRAY['food','tech','clothes','travel','health'])[1 + floor(random()*5)::int],
    round((10 + random()*990)::numeric, 2),
    -- платежи за последние 7 дней, включая сегодняшний
    date_trunc('day', now()) - (n || ' day')::interval
        + (random() * interval '24 hours')
FROM generate_series(0, 6) AS n
CROSS JOIN generate_series(1, 50);

INSERT INTO raw_users (category, balance)
SELECT
    (ARRAY['food','tech','clothes','travel','health'])[1 + floor(random()*5)::int],
    round((100 + random()*9900)::numeric, 2)
FROM generate_series(1, 200)
ON CONFLICT DO NOTHING;
