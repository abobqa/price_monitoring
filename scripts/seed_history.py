#!/usr/bin/env python3

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from etl.analytics import refresh_price_history
from etl.load import load_staging_to_db
from etl.transform import transform_raw_to_staging
from ingestion.run_ingestion import run_all


def main() -> None:
    for i in range(3):
        print(f"--- Run {i + 1}/3 ---")
        run_all()
        staging = transform_raw_to_staging()
        load_staging_to_db(staging)
        refresh_price_history()
    print("Seed complete. Open Streamlit dashboard.")


if __name__ == "__main__":
    main()
