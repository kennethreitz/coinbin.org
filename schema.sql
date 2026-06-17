-- Price-history table read by /history (server.py) and /forecast
-- (predictions.py), and written by the ingestion worker (ingest.py).
--
-- Historically this table was created out-of-band by a separate Heroku
-- process that is not in this repo; it is committed here so the schema is
-- explicit and reproducible.

CREATE TABLE IF NOT EXISTS api_coin (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    date  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS api_coin_name_date_idx ON api_coin (name, date DESC);
