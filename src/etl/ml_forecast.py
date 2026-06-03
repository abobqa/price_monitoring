from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LinearRegression
from sqlalchemy import text

from db.connection import get_engine


def forecast_product_price(product_id: int, horizon_days: int = 7) -> pd.DataFrame | None:
    engine = get_engine()
    hist = pd.read_sql(
        text(
            """
            SELECT history_date, avg_price
            FROM price_history
            WHERE product_id = :pid
            ORDER BY history_date
            """
        ),
        engine,
        params={"pid": product_id},
    )
    if len(hist) < 3:
        return None

    hist["history_date"] = pd.to_datetime(hist["history_date"])
    hist["t"] = (hist["history_date"] - hist["history_date"].min()).dt.days
    X = hist[["t"]].values
    y = hist["avg_price"].astype(float).values

    model = LinearRegression()
    model.fit(X, y)

    last_t = int(hist["t"].max())
    future = pd.DataFrame({"t": [last_t + d for d in range(1, horizon_days + 1)]})
    future["predicted_price"] = model.predict(future[["t"]])
    future["product_id"] = product_id
    return future
