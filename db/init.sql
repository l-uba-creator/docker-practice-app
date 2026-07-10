-- Init-схема для образа docker-practice-app-db.
-- Скрипт выполняется postgres-точкой входа при первом старте контейнера.
CREATE TABLE IF NOT EXISTS visits (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO visits (message)
VALUES ('База данных инициализирована')
ON CONFLICT DO NOTHING;
