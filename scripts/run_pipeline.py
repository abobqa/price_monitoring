#!/usr/bin/env python3

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alerts.notifier import check_price_alerts
from etl.analytics import refresh_price_history
from etl.load import load_staging_to_db
from etl.transform import transform_raw_to_staging
from ingestion.run_ingestion import run_all


def main() -> None:
    print("=== 1. Ingest ===")
    print(run_all())
    print("=== 2. Transform ===")
    staging = transform_raw_to_staging()
    print(staging)
    print("=== 3. Load ===")
    n = load_staging_to_db(staging)
    print(f"Loaded: {n}")
    print("=== 4. Analytics ===")
    h = refresh_price_history()
    print(f"History rows: {h}")
    print("=== 5. Alerts ===")
    alerts = check_price_alerts()
    print(f"Alerts sent: {len(alerts)}")


if __name__ == "__main__":
    main()
