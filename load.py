"""Fetch macro series from FRED and upsert them into PostgreSQL."""

import datetime as dt
import os
import time

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

API_KEY = os.environ["FRED_API_KEY"]
FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
RETRYABLE = {429, 500, 502, 503, 504}

engine = create_engine(os.environ["DATABASE_URL"])

SERIES = {
    # ticker: (name, frequency, unit)
    "CPIAUCSL": ("US consumer prices (CPI), seasonally adjusted", "M", "index"),
    "UNRATE": ("US unemployment rate", "M", "percent"),
    "FEDFUNDS": ("US federal funds rate, monthly average", "M", "percent"),
    "DGS2": ("US 2-year Treasury yield", "D", "percent"),
    "DGS10": ("US 10-year Treasury yield", "D", "percent"),
}

UPSERT_SERIES = text(
    """
    INSERT INTO series (series_id, name, frequency, unit)
    VALUES (:series_id, :name, :frequency, :unit)
    ON CONFLICT (series_id) DO UPDATE
    SET name = EXCLUDED.name, frequency = EXCLUDED.frequency, unit = EXCLUDED.unit
    """
)

UPSERT_OBSERVATION = text(
    """
    INSERT INTO observation (series_id, obs_date, value)
    VALUES (:series_id, :obs_date, :value)
    ON CONFLICT (series_id, obs_date) DO UPDATE
    SET value = EXCLUDED.value, loaded_at = now()
    """
)


def fetch(ticker: str, retries: int = 4) -> list[dict]:
    """Return FRED observations for one series, retrying temporary failures."""
    params = {
        "series_id": ticker,
        "api_key": API_KEY,
        "file_type": "json",
    }

    for attempt in range(retries):
        try:
            resp = requests.get(FRED_URL, params=params, timeout=30)
        except (requests.ConnectionError, requests.Timeout):
            resp = None

        if resp is not None:
            if resp.ok:
                return resp.json()["observations"]
            if resp.status_code not in RETRYABLE:
                resp.raise_for_status()

        if attempt < retries - 1:
            time.sleep(2**attempt)

    raise RuntimeError(f"{ticker}: gave up after {retries} attempts")


def main() -> None:
    for ticker, (name, frequency, unit) in SERIES.items():
        observations = fetch(ticker)
        rows = [
            {
                "series_id": ticker,
                "obs_date": dt.date.fromisoformat(observation["date"]),
                "value": (
                    None
                    if observation["value"] == "."
                    else float(observation["value"])
                ),
            }
            for observation in observations
        ]

        with engine.begin() as conn:
            conn.execute(
                UPSERT_SERIES,
                {
                    "series_id": ticker,
                    "name": name,
                    "frequency": frequency,
                    "unit": unit,
                },
            )
            conn.execute(UPSERT_OBSERVATION, rows)

        print(f"{ticker}: {len(rows):,} rows")


if __name__ == "__main__":
    main()
