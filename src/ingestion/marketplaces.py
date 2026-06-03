from __future__ import annotations

import logging

import requests
from bs4 import BeautifulSoup

from ingestion.base import BaseCollector, RawProductRecord
from ingestion.demo_data import build_demo_records

logger = logging.getLogger(__name__)


class WildberriesCollector(BaseCollector):
    source_name = "wildberries"

    def collect(self) -> list[RawProductRecord]:
        if self.mode != "live":
            return build_demo_records(self.source_name)

        try:
            return self._parse_search_page()
        except Exception as exc:
            logger.warning("WB live failed, fallback to demo: %s", exc)
            return build_demo_records(self.source_name)

    def _parse_search_page(self) -> list[RawProductRecord]:
        # пример статической выдачи поиска
        url = "https://www.wildberries.ru/catalog/0/search.aspx?search=смартфон"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; PriceMonitoring/1.0)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select("[data-nm-id]")[:5]
        if not cards:
            raise ValueError("No product cards parsed")
        records: list[RawProductRecord] = []
        for idx, card in enumerate(cards):
            nm_id = card.get("data-nm-id", f"wb-{idx}")
            name_el = card.select_one(".product-card__name, .goods-name")
            price_el = card.select_one(".price__lower-price, ins")
            name = name_el.get_text(strip=True) if name_el else f"WB product {nm_id}"
            price_text = price_el.get_text(strip=True) if price_el else "0"
            price = float("".join(ch for ch in price_text if ch.isdigit()) or 0)
            records.append(
                RawProductRecord(
                    external_id=str(nm_id),
                    name=name,
                    category="unknown",
                    brand="unknown",
                    source=self.source_name,
                    price=price,
                )
            )
        return records or build_demo_records(self.source_name)


class OzonCollector(BaseCollector):
    source_name = "ozon"

    def collect(self) -> list[RawProductRecord]:
        if self.mode != "live":
            return build_demo_records(self.source_name)
        try:
            return self._parse_search()
        except Exception as exc:
            logger.warning("Ozon live failed, fallback to demo: %s", exc)
            return build_demo_records(self.source_name)

    def _parse_search(self) -> list[RawProductRecord]:
        url = "https://www.ozon.ru/search/?text=ноутбук"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; PriceMonitoring/1.0)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        tiles = soup.select("[data-widget='searchResultsV2'] a")[:5]
        if not tiles:
            raise ValueError("No Ozon tiles parsed")
        records: list[RawProductRecord] = []
        for idx, tile in enumerate(tiles):
            records.append(
                RawProductRecord(
                    external_id=f"oz-{idx}",
                    name=tile.get_text(strip=True)[:200] or f"Ozon product {idx}",
                    category="unknown",
                    brand="unknown",
                    source=self.source_name,
                    price=0.0,
                    availability=True,
                )
            )
        return records


class YandexMarketCollector(BaseCollector):
    source_name = "yandex_market"

    def collect(self) -> list[RawProductRecord]:
        if self.mode != "live":
            return build_demo_records(self.source_name)
        try:
            return self._parse_search()
        except Exception as exc:
            logger.warning("Yandex Market live failed, fallback to demo: %s", exc)
            return build_demo_records(self.source_name)

    def _parse_search(self) -> list[RawProductRecord]:
        url = "https://market.yandex.ru/search?text=наушники"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; PriceMonitoring/1.0)"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        articles = soup.select("article")[:5]
        if not articles:
            raise ValueError("No Market articles parsed")
        records: list[RawProductRecord] = []
        for idx, art in enumerate(articles):
            title = art.select_one("h3, span[data-auto='snippet-title']")
            records.append(
                RawProductRecord(
                    external_id=f"ym-{idx}",
                    name=(title.get_text(strip=True) if title else f"YM product {idx}"),
                    category="unknown",
                    brand="unknown",
                    source=self.source_name,
                    price=0.0,
                )
            )
        return records
