from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from config.settings import settings
from db.connection import session_scope
from db.models import Price, Product


def upsert_product(session, row: pd.Series) -> int:
    stmt = insert(Product).values(
        external_id=str(row["external_id"]),
        name=str(row["name"]),
        category=str(row.get("category") or ""),
        brand=str(row.get("brand") or ""),
        source=str(row["source"]),
        updated_at=datetime.now(timezone.utc),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["external_id", "source"],
        set_={
            "name": str(row["name"]),
            "category": str(row.get("category") or ""),
            "brand": str(row.get("brand") or ""),
            "updated_at": datetime.now(timezone.utc),
        },
    ).returning(Product.product_id)
    result = session.execute(stmt).scalar_one()
    return int(result)


def load_staging_to_db(staging_path: Path | None = None) -> int:
    path = staging_path or (settings.processed_data_dir / "staging_prices.parquet")
    df = pd.read_parquet(path)
    loaded = 0
    with session_scope() as session:
        for _, row in df.iterrows():
            product_id = upsert_product(session, row)
            collected = row.get("_collected_at")
            if pd.isna(collected):
                collected_at = datetime.now(timezone.utc)
            else:
                collected_at = pd.to_datetime(collected, utc=True).to_pydatetime()

            price_row = Price(
                product_id=product_id,
                price=Decimal(str(round(float(row["price"]), 2))),
                price_rub=Decimal(str(round(float(row.get("price_rub", row["price"])), 2))),
                currency=str(row.get("currency", "RUB")),
                collected_at=collected_at,
                availability=bool(row.get("availability", True)),
                raw_payload=json.loads(
                    json.dumps(
                        {
                            "raw_file": row.get("_raw_file"),
                            "name_normalized": row.get("name_normalized"),
                        },
                        default=str,
                    )
                ),
            )
            session.add(price_row)
            loaded += 1
    return loaded


if __name__ == "__main__":
    count = load_staging_to_db()
    print(f"Loaded {count} price rows")
