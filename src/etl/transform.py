from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from config.settings import settings
from ingestion.currency_api import fetch_rates


def normalize_product_name(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^\w\sа-яё\-]", "", name, flags=re.IGNORECASE)
    return name.title()


def load_raw_files() -> pd.DataFrame:
    rows: list[dict] = []
    raw_root = settings.raw_data_dir
    for path in sorted(raw_root.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for rec in payload.get("records", []):
            rec["_raw_file"] = str(path)
            rec["_collected_at"] = payload.get("collected_at")
            rows.append(rec)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def apply_currency_conversion(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    try:
        rates = fetch_rates(base=settings.currency_base, symbols=["USD", "EUR", "RUB"])
    except Exception:
        rates = {"RUB": 1.0, "USD": 1.0, "EUR": 1.0}

    def to_rub(row: pd.Series) -> float:
        cur = str(row.get("currency", "RUB")).upper()
        price = float(row["price"])
        if cur == "RUB":
            return price
        if cur not in rates or settings.currency_base not in rates:
            return price
        base = settings.currency_base
        if cur == base:
            amount_base = price
        else:
            amount_base = price / rates[cur] if rates[cur] else price
        rub_rate = rates.get("RUB", 1.0)
        base_rate = rates.get(base, 1.0)
        return round(amount_base * (rub_rate / base_rate), 2)

    df = df.copy()
    df["price_rub"] = df.apply(to_rub, axis=1)
    df["name_normalized"] = df["name"].astype(str).map(normalize_product_name)
    return df


def deduplicate_latest(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.sort_values("_collected_at", ascending=False)
    return df.drop_duplicates(subset=["external_id", "source"], keep="first")


def transform_raw_to_staging() -> Path:
    df = load_raw_files()
    if df.empty:
        raise FileNotFoundError(f"No raw JSON in {settings.raw_data_dir}")

    df = apply_currency_conversion(df)
    df = deduplicate_latest(df)

    out = settings.processed_data_dir / "staging_prices.parquet"
    df.to_parquet(out, index=False)
    return out


if __name__ == "__main__":
    path = transform_raw_to_staging()
    print(f"Staging saved: {path}")
