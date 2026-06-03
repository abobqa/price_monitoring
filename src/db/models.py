from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("external_id", "source"),)

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128))
    brand: Mapped[str | None] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    prices: Mapped[list["Price"]] = relationship(back_populates="product")


class Price(Base):
    __tablename__ = "prices"

    price_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price_rub: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8), default="RUB")
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    availability: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)

    product: Mapped["Product"] = relationship(back_populates="prices")


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("product_id", "history_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    history_date: Mapped[date] = mapped_column(Date, nullable=False)
    min_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    max_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    avg_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    availability_status: Mapped[str | None] = mapped_column(String(32))
    observations_count: Mapped[int | None] = mapped_column(Integer, default=0)


class RawIngestionLog(Base):
    __tablename__ = "raw_ingestion_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    records_count: Mapped[int | None] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)


class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    __table_args__ = (UniqueConstraint("base_currency", "target_currency", "rate_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_currency: Mapped[str] = mapped_column(String(8), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(8), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, nullable=False)
