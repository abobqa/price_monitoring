-- Application database: price_monitoring
-- Airflow uses the same Postgres instance with DB "airflow"

CREATE DATABASE airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO de_user;

\c price_monitoring;

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS products (
    product_id   SERIAL PRIMARY KEY,
    external_id  VARCHAR(128),
    name           VARCHAR(512) NOT NULL,
    category       VARCHAR(128),
    brand          VARCHAR(128),
    source         VARCHAR(64) NOT NULL,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (external_id, source)
);

CREATE TABLE IF NOT EXISTS prices (
    price_id       SERIAL PRIMARY KEY,
    product_id     INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    price          NUMERIC(12, 2) NOT NULL,
    price_rub      NUMERIC(12, 2),
    currency       VARCHAR(8) NOT NULL DEFAULT 'RUB',
    collected_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    availability   BOOLEAN NOT NULL DEFAULT TRUE,
    raw_payload    JSONB
);

CREATE INDEX IF NOT EXISTS idx_prices_product_collected
    ON prices (product_id, collected_at DESC);

CREATE TABLE IF NOT EXISTS price_history (
    id                   SERIAL PRIMARY KEY,
    product_id           INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    history_date         DATE NOT NULL,
    min_price            NUMERIC(12, 2),
    max_price            NUMERIC(12, 2),
    avg_price            NUMERIC(12, 2),
    availability_status  VARCHAR(32),
    observations_count   INTEGER DEFAULT 0,
    UNIQUE (product_id, history_date)
);

CREATE TABLE IF NOT EXISTS raw_ingestion_log (
    id            SERIAL PRIMARY KEY,
    source        VARCHAR(64) NOT NULL,
    file_path     TEXT,
    status        VARCHAR(32) NOT NULL,
    records_count INTEGER DEFAULT 0,
    error_message TEXT,
    ingested_at   TIMESTAMPTZ DEFAULT NOW(),
    metadata      JSONB
);

CREATE TABLE IF NOT EXISTS currency_rates (
    id           SERIAL PRIMARY KEY,
    base_currency VARCHAR(8) NOT NULL,
    target_currency VARCHAR(8) NOT NULL,
    rate         NUMERIC(18, 8) NOT NULL,
    rate_date    DATE NOT NULL,
    UNIQUE (base_currency, target_currency, rate_date)
);

CREATE OR REPLACE VIEW v_latest_prices AS
SELECT DISTINCT ON (px.product_id)
    px.product_id,
    pr.name,
    pr.category,
    pr.brand,
    pr.source,
    px.price,
    px.price_rub,
    px.currency,
    px.collected_at,
    px.availability
FROM prices px
JOIN products pr ON pr.product_id = px.product_id
ORDER BY px.product_id, px.collected_at DESC;
