from __future__ import annotations

import logging

import requests

from config.settings import settings
from etl.analytics import price_change_leaders

logger = logging.getLogger(__name__)


def send_telegram(message: str) -> bool:
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id
    if not token or not chat_id:
        logger.info("Telegram not configured, alert skipped")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=15)
    resp.raise_for_status()
    return True


def check_price_alerts() -> list[str]:
    df = price_change_leaders(limit=50)
    if df.empty:
        return []
    threshold = settings.alert_price_change_pct
    alerts: list[str] = []
    for _, row in df.iterrows():
        pct = float(row.get("change_pct") or 0)
        if abs(pct) >= threshold:
            direction = "выросла" if pct > 0 else "упала"
            msg = (
                f"Цена {direction} на {abs(pct):.1f}%\n"
                f"{row['name']} ({row['source']})\n"
                f"Было: {row['price_prev']} ₽ → Сейчас: {row['price_latest']} ₽"
            )
            alerts.append(msg)
            try:
                send_telegram(msg)
            except Exception as exc:
                logger.warning("Telegram send failed: %s", exc)
    return alerts
