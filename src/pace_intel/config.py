from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://pace:devpassword@localhost:5432/pace_intel"
    database_url_sync: str = "postgresql+psycopg2://pace:devpassword@localhost:5432/pace_intel"

    # Storage
    raw_data_dir: Path = Path("./data/raw")

    # Rate limits (requests per second, per source)
    rate_limit_recorder: float = 0.5
    rate_limit_assessor: float = 0.5
    rate_limit_caeatfa: float = 1.0
    rate_limit_dfpi: float = 1.0

    # Observability
    prometheus_port: int = 8001

    # Optional tokens
    riverside_socrata_token: str = ""

    # Prefect
    prefect_api_url: str = "http://localhost:4200/api"

    @property
    def is_production(self) -> bool:
        return self.env == "production"


settings = Settings()
