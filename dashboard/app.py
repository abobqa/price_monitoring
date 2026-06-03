from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from db.connection import get_engine
from etl.analytics import category_avg_prices, price_change_leaders
from etl.ml_forecast import forecast_product_price

st.set_page_config(page_title="Мониторинг цен", layout="wide")
st.title("Мониторинг цен товаров")
st.caption("Pet-проект: Wildberries, Ozon, Яндекс.Маркет, offline CSV и Frankfurter API")

engine = get_engine()

@st.cache_data(ttl=300)
def load_filters() -> dict:
    df = pd.read_sql(
        text("SELECT DISTINCT source, brand, category FROM products ORDER BY 1,2,3"),
        engine,
    )
    return {
        "sources": ["Все"] + sorted(df["source"].dropna().unique().tolist()),
        "brands": ["Все"] + sorted(df["brand"].dropna().unique().tolist()),
        "categories": ["Все"] + sorted(df["category"].dropna().unique().tolist()),
    }


filters = load_filters()
col1, col2, col3 = st.columns(3)
source = col1.selectbox("Магазин", filters["sources"])
brand = col2.selectbox("Бренд", filters["brands"])
category = col3.selectbox("Категория", filters["categories"])

where = ["1=1"]
params: dict = {}
if source != "Все":
    where.append("pr.source = :source")
    params["source"] = source
if brand != "Все":
    where.append("pr.brand = :brand")
    params["brand"] = brand
if category != "Все":
    where.append("pr.category = :category")
    params["category"] = category
where_sql = " AND ".join(where)

latest = pd.read_sql(
    text(
        f"""
        SELECT pr.product_id, pr.name, pr.brand, pr.category, pr.source,
               px.price_rub, px.availability, px.collected_at
        FROM products pr
        JOIN LATERAL (
            SELECT price_rub, availability, collected_at
            FROM prices
            WHERE product_id = pr.product_id
            ORDER BY collected_at DESC
            LIMIT 1
        ) px ON TRUE
        WHERE {where_sql}
        ORDER BY px.collected_at DESC
        """
    ),
    engine,
    params=params,
)

st.subheader("Актуальные цены")
st.dataframe(latest, use_container_width=True)

history = pd.read_sql(
    text(
        f"""
        SELECT ph.history_date, pr.name, pr.source, pr.brand, pr.category,
               ph.avg_price, ph.min_price, ph.max_price
        FROM price_history ph
        JOIN products pr ON pr.product_id = ph.product_id
        WHERE {where_sql.replace('pr.', 'pr.')}
        ORDER BY ph.history_date
        """
    ),
    engine,
    params=params,
)

st.subheader("Динамика средней цены")
if history.empty:
    st.info("Запустите пайплайн: `python scripts/run_pipeline.py` или `python scripts/seed_history.py`")
else:
    fig = px.line(
        history,
        x="history_date",
        y="avg_price",
        color="name",
        markers=True,
        labels={"history_date": "Дата", "avg_price": "Средняя цена, ₽"},
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Топ-10: рост / падение цены")
leaders = price_change_leaders(10)
if not leaders.empty:
    st.dataframe(leaders, use_container_width=True)
    fig2 = px.bar(
        leaders,
        x="name",
        y="change_pct",
        color="source",
        labels={"change_pct": "Изменение, %"},
    )
    fig2.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Средняя цена по категориям")
cat_avg = category_avg_prices()
if not cat_avg.empty:
    fig3 = px.bar(
        cat_avg,
        x="category",
        y="avg_price_rub",
        color="source",
        barmode="group",
        labels={"avg_price_rub": "Средняя цена, ₽"},
    )
    st.plotly_chart(fig3, use_container_width=True)

st.subheader("Прогноз цены (Linear Regression)")
product_ids = latest["product_id"].tolist() if not latest.empty else []
if product_ids:
    pid = st.selectbox(
        "Товар",
        product_ids,
        format_func=lambda x: latest.loc[latest["product_id"] == x, "name"].iloc[0],
    )
    forecast = forecast_product_price(int(pid))
    if forecast is not None:
        st.line_chart(forecast.set_index("t")["predicted_price"])
    else:
        st.warning("Недостаточно истории (нужно ≥ 3 дней). Запустите seed_history.")
