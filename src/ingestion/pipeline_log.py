from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert

from db.connection import session_scope
from db.models import RawIngestionLog


def log_ingestion_batch(
    source: str,
    file_path: str,
    status: str,
    records_count: int = 0,
    error_message: str | None = None,
    metadata: dict | None = None,
) -> None:
    with session_scope() as session:
        session.execute(
            insert(RawIngestionLog).values(
                source=source,
                file_path=file_path,
                status=status,
                records_count=records_count,
                error_message=error_message,
                ingested_at=datetime.now(timezone.utc),
                metadata_=metadata,
            )
        )
