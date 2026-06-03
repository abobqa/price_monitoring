from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import text

from config.settings import settings
from db.connection import get_engine, session_scope
from db.models import PriceHistory


def refresh_price_history(target_date: date | None = None) -> int:
    target_date = target_date or date.today()
    engine = get_engine()
    query = text(
        """
        SELECT
            product_id,
            :target_date AS history_date,
            MIN(price_rub) AS min_price,
            MAX(price_rub) AS max_price,
            AVG(price_rub) AS avg_price,
            CASE
                WHEN BOOL_OR(availability) THEN 'in_stock'
                ELSE 'out_of_stock'
            END AS availability_status,
            COUNT(*) AS observations_count
        FROM prices
        WHERE collected_at::date = :target_date
        GROUP BY product_id
        """
    )
    df = pd.read_sql(query, engine, params={"target_date": target_date})
    if df.empty:
        return 0

    rows = 0
    with session_scope() as session:
        for _, row in df.iterrows():
            existing = (
                session.query(PriceHistory)
                .filter_by(product_id=int(row["product_id"]), history_date=target_date)
                .one_or_none()
            )
            payload = {
                "min_price": row["min_price"],
                "max_price": row["max_price"],
                "avg_price": row["avg_price"],
                "availability_status": row["availability_status"],
                "observations_count": int(row["observations_count"]),
            }
            if existing:
                for k, v in payload.items():
                    setattr(existing, k, v)
            else:
                session.add(
                    PriceHistory(
                        product_id=int(row["product_id"]),
                        history_date=target_date,
                        **payload,
                    )
                )
            rows += 1
    return rows


def category_avg_prices() -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql(
        text(
            """
            SELECT pr.category, pr.source,
                   ROUND(AVG(px.price_rub)::numeric, 2) AS avg_price_rub,
                   COUNT(DISTINCT pr.product_id) AS products_count
            FROM products pr
            JOIN prices px ON px.product_id = pr.product_id
            WHERE px.collected_at >= NOW() - INTERVAL '30 days'
            GROUP BY pr.category, pr.source
            ORDER BY avg_price_rub DESC
            """
        ),
        engine,
    )


def price_change_leaders(limit: int = 10) -> pd.DataFrame:
    """Топ товаров по изменению цены между двумя последними срезами."""
    engine = get_engine()
    return pd.read_sql(
        text(
            """
            WITH ranked AS (
                SELECT
                    px.product_id,
                    pr.name,
                    pr.brand,
                    pr.category,
                    pr.source,
                    px.price_rub,
                    px.collected_at,
                    ROW_NUMBER() OVER (
                        PARTITION BY px.product_id ORDER BY px.collected_at DESC
                    ) AS rn
                FROM prices px
                JOIN products pr ON pr.product_id = px.product_id
            ),
            last_two AS (
                SELECT
                    product_id, name, brand, category, source,
                    MAX(CASE WHEN rn = 1 THEN price_rub END) AS price_latest,
                    MAX(CASE WHEN rn = 2 THEN price_rub END) AS price_prev
                FROM ranked
                WHERE rn <= 2
                GROUP BY product_id, name, brand, category, source
            )
            SELECT *,
                   ROUND((price_latest - price_prev)::numeric, 2) AS price_delta,
                   ROUND(
                       100.0 * (price_latest - price_prev) / NULLIF(price_prev, 0),
                       2
                   ) AS change_pct
            FROM last_two
            WHERE price_prev IS NOT NULL AND price_latest IS NOT NULL
            ORDER BY change_pct DESC NULLS LAST
            LIMIT :limit
            """
        ),
        engine,
        params={"limit": limit},
    )


if __name__ == "__main__":
    n = refresh_price_history()
    print(f"Updated {n} price_history rows")
