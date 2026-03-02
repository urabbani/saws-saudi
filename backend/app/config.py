"""
SAWS Configuration Management

Saudi AgriDrought Warning System
Configuration settings with environment variable support
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "SAWS API"
    app_version: str = "0.1.0"
    app_description: str = "Saudi AgriDrought Warning System API"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # API
    api_v1_prefix: str = "/api/v1"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # Security
    secret_key: str = Field(default="change-this-in-production", min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "saws_user"
    db_password: str = "saws_password"
    db_name: str = "saws_db"
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def sync_database_url(self) -> str:
        """Construct synchronous database URL for migrations."""
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_pool_size: int = 10

    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Celery
    celery_broker_url: str | None = None  # Defaults to redis_url
    celery_result_backend: str | None = None  # Defaults to redis_url
    celery_task_time_limit: int = 3600  # 1 hour
    celery_task_soft_time_limit: int = 3000  # 50 minutes

    # Google Earth Engine
    gee_service_account_key_path: str | None = None
    gee_project_id: str | None = None

    # Satellite Data Sources
    modis_collection_id: str = "MODIS/006/MOD13Q1"
    landsat_collection_id: str = "LANDSAT/LC08/C02/T1_L2"
    sentinel1_collection_id: str = "COPERNICUS/S1_GRD"
    sentinel2_collection_id: str = "COPERNICUS/S2_SR_HARMONIZED"

    # Saudi Arabia Region Bounds (Eastern Province)
    # Accurate bounds for Eastern Province: Extends from Hafar Al-Batin to UAE border
    eastern_province_bounds: tuple[float, float, float, float] = (
        45.0,   # West longitude (Hafar Al-Batin area)
        24.0,   # South latitude (Rub' al-Khali border)
        55.0,   # East longitude (Saudi/UAE border area)
        28.0,   # North latitude (Northern EP border)
    )

    # Major agricultural districts in Eastern Province
    eastern_province_districts: dict[str, tuple[float, float, float, float]] = {
        "al_ahsa": (49.5, 25.0, 50.0, 26.0),      # Al-Hasa Oasis (corrected lat)
        "qatif": (50.0, 26.0, 50.5, 26.6),         # Al-Qatif
        "hofuf": (49.3, 25.0, 49.8, 25.6),         # Al-Hofuf
        "dammam": (50.0, 26.2, 50.5, 26.5),         # Dammam area
        "khobar": (50.2, 26.2, 50.5, 26.5),         # Al-Khobar
        "jubail": (49.5, 26.8, 50.2, 27.2),         # Al-Jubail
        "hafar_al_batin": (45.5, 27.5, 46.5, 28.5), # Hafar Al-Batin (now within bounds)
    }

    # Weather API (PME - Presidency of Meteorology and Environment)
    pme_api_key: str | None = None
    pme_api_base_url: str = "https://api.pme.gov.sa"

    # Alert Settings
    alert_retention_days: int = 365
    alert_email_enabled: bool = True
    alert_sms_enabled: bool = False
    alert_whatsapp_enabled: bool = False

    # SMTP Configuration
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "noreply@saws.gov.sa"
    smtp_from_name: str = "SAWS Alerts"

    # SMS Configuration
    sms_provider: Literal["twilio", "custom"] = "custom"
    sms_api_key: str | None = None

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # File Storage
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    raw_data_dir: Path = Field(default_factory=lambda: Path("data/raw"))
    processed_data_dir: Path = Field(default_factory=lambda: Path("data/processed"))
    models_dir: Path = Field(default_factory=lambda: Path("data/models"))

    # Monitoring
    enable_prometheus: bool = True
    prometheus_multiproc_dir: str = "/tmp"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"
    log_file: Path | None = None

    # Compliance (Saudi Government)
    data_localization_required: bool = True  # PDPL compliance
    audit_log_retention_days: int = 365 * 5  # 5 years
    encryption_at_rest: bool = True
    tls_min_version: str = "1.3"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # Background Tasks
    satellite_fetch_interval_hours: int = 24
    weather_fetch_interval_hours: int = 6
    drought_calculation_interval_hours: int = 12

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is not default in production."""
        if v == "change-this-in-production":
            import warnings

            warnings.warn("Using default secret key. Change this in production!")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Settings instance for import
settings = get_settings()
