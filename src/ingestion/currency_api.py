from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

import requests
from sqlalchemy.dialects.postgresql import insert

from config.settings import settings
from db.connection import session_scope
from db.models import CurrencyRate

logger = logging.getLogger(__name__)


FRANKFURTER_URL = "https://api.frankfurter.app/latest"


def fetch_rates(base: str | None = None, symbols: list[str] | None = None) -> dict[str, float]:
    base = base or settings.currency_base
    params: dict[str, str] = {"from": base}
    if symbols:
        params["to"] = ",".join(symbols)
    resp = requests.get(FRANKFURTER_URL, params=params, timeout=15)
    if resp.status_code == 404 and base != "EUR":
        params["from"] = "EUR"
        if symbols and base not in symbols:
            symbols = list(symbols) + [base]
        params["to"] = ",".join(symbols) if symbols else base
        resp = requests.get(FRANKFURTER_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    rates = data.get("rates", {})
    rates[data.get("base", base)] = 1.0
    return {k: float(v) for k, v in rates.items()}


def save_rates_to_db(rates: dict[str, float], base: str, rate_date: date | None = None) -> int:
    rate_date = rate_date or date.today()
    rows = 0
    with session_scope() as session:
        for target, rate in rates.items():
            if target == base:
                continue
            stmt = insert(CurrencyRate).values(
                base_currency=base,
                target_currency=target,
                rate=Decimal(str(rate)),
                rate_date=rate_date,
            )
            stmt = stmt.on_conflict_do_update(
                constraint="currency_rates_base_currency_target_currency_rate_date_key",
                set_={"rate": Decimal(str(rate))},
            )
            session.execute(stmt)
            rows += 1
    return rows


def convert_to_rub(amount: float, currency: str, rates: dict[str, float] | None = None) -> float:
    currency = currency.upper()
    if currency == "RUB":
        return amount
    rates = rates or fetch_rates(base="EUR", symbols=["RUB", "USD", currency])
    # frankfurter base EUR in fallback
    rates = rates or fetch_rates(base=settings.currency_base)
    if currency == settings.currency_base:
        return amount
    # amount in CUR - base - RUB
    base = settings.currency_base
    if currency not in rates or base not in rates:
        return amount
    in_base = amount / rates[currency] if currency != base else amount
    return round(in_base * rates.get("RUB", rates.get(base, 1.0)), 2)


def run_currency_ingestion() -> dict:
    try:
        rates = fetch_rates(base=settings.currency_base, symbols=["USD", "EUR", "RUB"])
        saved = save_rates_to_db(rates, settings.currency_base)
        return {
            "status": "success",
            "saved": saved,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.exception("Currency ingestion failed")
        return {"status": "error", "error": str(exc)}
