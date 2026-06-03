from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import settings


@dataclass
class RawProductRecord:
    external_id: str
    name: str
    category: str
    brand: str
    source: str
    price: float
    currency: str = "RUB"
    availability: bool = True
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseCollector(ABC):
    source_name: str

    def __init__(self, mode: str | None = None) -> None:
        self.mode = mode or settings.ingest_mode

    @abstractmethod
    def collect(self) -> list[RawProductRecord]:
        raise NotImplementedError

    def save_raw(self, records: list[RawProductRecord]) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_dir = settings.raw_data_dir / self.source_name
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{self.source_name}_{ts}.json"
        payload = {
            "source": self.source_name,
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "status": "success",
            "records_count": len(records),
            "records": [r.to_dict() for r in records],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def run(self) -> tuple[Path, list[RawProductRecord]]:
        records = self.collect()
        path = self.save_raw(records)
        return path, records
