from __future__ import annotations

import logging
from datetime import datetime, timezone

from ingestion.base import BaseCollector
from ingestion.csv_loader import OfflineCsvCollector
from ingestion.currency_api import run_currency_ingestion
from ingestion.marketplaces import (
    OzonCollector,
    WildberriesCollector,
    YandexMarketCollector,
)
from ingestion.pipeline_log import log_ingestion_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

COLLECTORS: list[BaseCollector] = [
    WildberriesCollector(),
    OzonCollector(),
    YandexMarketCollector(),
    OfflineCsvCollector(),
]


def run_all() -> dict:
    summary = {"sources": [], "currency": None, "started_at": datetime.now(timezone.utc).isoformat()}
    for collector in COLLECTORS:
        path, records = collector.run()
        log_ingestion_batch(collector.source_name, str(path), "success", len(records))
        summary["sources"].append(
            {"source": collector.source_name, "file": str(path), "records": len(records)}
        )
        logger.info("%s: %s records -> %s", collector.source_name, len(records), path)

    summary["currency"] = run_currency_ingestion()
    summary["finished_at"] = datetime.now(timezone.utc).isoformat()
    return summary


if __name__ == "__main__":
    print(run_all())
