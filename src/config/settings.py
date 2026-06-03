from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "price_monitoring"
    postgres_user: str = "de_user"
    postgres_password: str = "de_password"

    ingest_mode: str = "demo"
    raw_data_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_data_dir: Path = PROJECT_ROOT / "data" / "processed"
    currency_base: str = "RUB"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    alert_price_change_pct: float = 15.0

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
