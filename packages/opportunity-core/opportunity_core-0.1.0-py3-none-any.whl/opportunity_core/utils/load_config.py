import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Allow custom env file path via environment variable (for dev-once command)
# If ENV_FILE_PATH is set, use it; otherwise use .env
_env_file_path = os.environ.get("ENV_FILE_PATH")
ENV_FILE = PROJECT_ROOT / _env_file_path if _env_file_path else PROJECT_ROOT / ".env"


class PaapiConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    access_key: str = Field(alias="PAAPI_ACCESS_KEY")
    secret_key: str = Field(alias="PAAPI_SECRET_KEY")
    partner_tag: str = Field(alias="PAAPI_PARTNER_TAG")
    host: str = Field(alias="PAAPI_HOST")
    region: str = Field(alias="PAAPI_REGION")
    locale: str = Field(alias="PAAPI_LOCALE")
    partner_type: str = Field(alias="PAAPI_PARTNER_TYPE")
    marketplace: str = Field(alias="PAAPI_MARKETPLACE")


class TwitterConfig(BaseSettings):
    """Twitter API configuration for posting deal notifications."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    api_key: str = Field(alias="TWITTER_API_KEY")
    api_secret: str = Field(alias="TWITTER_API_SECRET")
    access_token: str = Field(alias="TWITTER_ACCESS_TOKEN")
    access_token_secret: str = Field(alias="TWITTER_ACCESS_TOKEN_SECRET")
    bearer_token: str = Field(default="", alias="TWITTER_BEARER_TOKEN")


class DealConfig(BaseSettings):
    """Configuration for deal detection and monitoring."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    min_discount_percentage: int = Field(default=10, alias="MIN_DISCOUNT_PERCENTAGE")
    check_interval_seconds: int = Field(default=300, alias="CHECK_INTERVAL_SECONDS")
    search_keywords: str = Field(default="laptop,telefon,kulaklık", alias="SEARCH_KEYWORDS")
    max_price: float = Field(default=10000.0, alias="MAX_PRICE")


class TelegramConfig(BaseSettings):
    """Telegram bot configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    channel_id: str = Field(..., alias="TELEGRAM_CHANNEL_ID")
    dev_channel_id: str = Field(default="", alias="TELEGRAM_DEV_CHANNEL_ID")

    def get_active_channel_id(self, environment: str = "production") -> str:
        """Get the appropriate channel ID based on environment."""
        if environment == "development" and self.dev_channel_id:
            return self.dev_channel_id
        return self.channel_id


class PlatformConfig(BaseSettings):
    """Platform enable/disable configuration."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    enable_twitter: bool = Field(default=False, alias="ENABLE_TWITTER")
    enable_telegram: bool = Field(default=True, alias="ENABLE_TELEGRAM")
    environment: str = Field(default="production", alias="ENVIRONMENT")

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"


class DatabaseConfig(BaseSettings):
    """Database configuration for PostgreSQL."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Full database URL (preferred)
    database_url: str = Field(
        default="postgresql://amazon_user:amazon_pass@localhost:5432/amazon_deals",
        alias="DATABASE_URL",
    )

    # Connection pooling
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")

    # Query settings
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    def get_database_url(self) -> str:
        """Get database URL."""
        return self.database_url


class MonitoringConfig(BaseSettings):
    """Monitoring and discovery configuration."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Product discovery
    search_keywords: str = Field(..., alias="SEARCH_KEYWORDS")
    max_pages_per_keyword: int = Field(default=3, alias="MAX_PAGES_PER_KEYWORD")

    # Monitoring intervals (in seconds)
    discovery_interval: int = Field(default=3600, alias="DISCOVERY_INTERVAL_SECONDS")

    # Price limits
    max_price: float = Field(default=50000.0, alias="MAX_PRICE")

    def get_keywords_list(self) -> list[str]:
        """Parse keywords string into list."""
        return [kw.strip() for kw in self.search_keywords.split(",") if kw.strip()]
