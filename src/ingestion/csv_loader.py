from pathlib import Path

import pandas as pd

from config.settings import PROJECT_ROOT
from ingestion.base import BaseCollector, RawProductRecord


class OfflineCsvCollector(BaseCollector):
    source_name = "offline_csv"

    def __init__(self, csv_path: Path | None = None, mode: str | None = None) -> None:
        super().__init__(mode=mode)
        self.csv_path = csv_path or (PROJECT_ROOT / "data" / "sample" / "offline_products.csv")

    def collect(self) -> list[RawProductRecord]:
        df = pd.read_csv(self.csv_path)
        records: list[RawProductRecord] = []
        for row in df.to_dict(orient="records"):
            records.append(
                RawProductRecord(
                    external_id=str(row["external_id"]),
                    name=str(row["name"]).strip(),
                    category=str(row.get("category", "")),
                    brand=str(row.get("brand", "")),
                    source=str(row.get("source", self.source_name)),
                    price=float(row["price"]),
                    currency=str(row.get("currency", "RUB")),
                    availability=bool(row.get("availability", True)),
                )
            )
        return records
