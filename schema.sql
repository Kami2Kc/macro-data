CREATE TABLE IF NOT EXISTS series (
series_id TEXT PRIMARY KEY,
name TEXT NOT NULL,
frequency TEXT NOT NULL,
unit TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observation (
series_id TEXT NOT NULL REFERENCES series (series_id),
obs_date DATE NOT NULL,
value NUMERIC,
loaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
PRIMARY KEY (series_id, obs_date)
);