"""Configuration module for iranleague_exporter."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Language(str, Enum):
    """Language enumeration for team names."""

    FA = "FA"
    EN = "EN"


@dataclass(frozen=True)
class HTTPConfig:
    """HTTP server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1


@dataclass(frozen=True)
class CrawlerConfig:
    """Crawler configuration."""

    url: str = "https://iranleague.ir/fa/MatchSchedule/1/1"
    connect_timeout: float = 5.0
    read_timeout: float = 10.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    user_agent: str = "IranLeagueExporter/1.0"


@dataclass(frozen=True)
class AuthConfig:
    """Authentication configuration."""

    username: str = ""
    password: str = ""

    def is_configured(self) -> bool:
        """Check if authentication is properly configured."""
        return bool(self.username and self.password)


@dataclass
class AppConfig:
    """Application configuration loaded from environment variables."""

    http: HTTPConfig = field(default_factory=HTTPConfig)
    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    log_level: LogLevel = LogLevel.INFO
    label_lang: Language = Language.EN
    update_interval_minutes: int = 30

    @property
    def update_interval_seconds(self) -> int:
        """Get update interval in seconds."""
        return self.update_interval_minutes * 60

    @classmethod
    def from_env(cls) -> AppConfig:
        """Load configuration from environment variables.

        Returns:
            AppConfig: Application configuration instance.

        Raises:
            ValueError: If required environment variables are missing or invalid.
        """
        return cls(
            http=HTTPConfig(
                host=os.getenv("HTTP_HOST", "0.0.0.0"),
                port=_get_int_env("HTTP_PORT", 8000),
                workers=_get_int_env("HTTP_WORKERS", 1),
            ),
            crawler=CrawlerConfig(
                url=os.getenv(
                    "CRAWLER_URL", "https://iranleague.ir/fa/MatchSchedule/1/1"
                ),
                connect_timeout=_get_float_env("CRAWLER_CONNECT_TIMEOUT", 5.0),
                read_timeout=_get_float_env("CRAWLER_READ_TIMEOUT", 10.0),
                max_retries=_get_int_env("CRAWLER_MAX_RETRIES", 3),
                retry_backoff_factor=_get_float_env("CRAWLER_RETRY_BACKOFF", 0.5),
                user_agent=os.getenv("CRAWLER_USER_AGENT", "IranLeagueExporter/1.0"),
            ),
            auth=AuthConfig(
                username=os.getenv("AUTH_USERNAME", ""),
                password=os.getenv("AUTH_PASSWORD", ""),
            ),
            log_level=_get_log_level_env("LOG_LEVEL", LogLevel.INFO),
            label_lang=_get_language_env("LABEL_LANG", Language.EN),
            update_interval_minutes=_get_int_env("UPDATE_INTERVAL", 30),
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors.

        Returns:
            list[str]: List of validation error messages.
        """
        errors: list[str] = []

        if not self.auth.is_configured():
            errors.append(
                "Authentication not configured: "
                "AUTH_USERNAME and AUTH_PASSWORD required"
            )

        if self.update_interval_minutes < 1:
            errors.append("UPDATE_INTERVAL must be at least 1 minute")

        if self.http.port < 1 or self.http.port > 65535:
            errors.append("HTTP_PORT must be between 1 and 65535")

        if self.crawler.connect_timeout <= 0:
            errors.append("CRAWLER_CONNECT_TIMEOUT must be positive")

        if self.crawler.read_timeout <= 0:
            errors.append("CRAWLER_READ_TIMEOUT must be positive")

        return errors


def _get_int_env(key: str, default: int) -> int:
    """Get integer environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        int: Environment variable value or default.

    Raises:
        ValueError: If value cannot be converted to int.
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as e:
        raise ValueError(f"Environment variable '{key}' must be an integer") from e


def _get_float_env(key: str, default: float) -> float:
    """Get float environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        float: Environment variable value or default.

    Raises:
        ValueError: If value cannot be converted to float.
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as e:
        raise ValueError(f"Environment variable '{key}' must be a number") from e


def _get_log_level_env(key: str, default: LogLevel) -> LogLevel:
    """Get log level environment variable.

    Args:
        key: Environment variable name.
        default: Default log level.

    Returns:
        LogLevel: Log level enumeration value.

    Raises:
        ValueError: If value is not a valid log level.
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return LogLevel(value.upper())
    except ValueError as e:
        valid_levels = ", ".join(level.value for level in LogLevel)
        raise ValueError(
            f"Environment variable '{key}' must be one of: {valid_levels}"
        ) from e


def _get_language_env(key: str, default: Language) -> Language:
    """Get language environment variable.

    Args:
        key: Environment variable name.
        default: Default language.

    Returns:
        Language: Language enumeration value.

    Raises:
        ValueError: If value is not a valid language.
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return Language(value.upper())
    except ValueError as e:
        valid_langs = ", ".join(lang.value for lang in Language)
        raise ValueError(
            f"Environment variable '{key}' must be one of: {valid_langs}"
        ) from e


# Global configuration instance (loaded lazily)
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get the application configuration singleton.

    Returns:
        AppConfig: Application configuration instance.
    """
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config


def reset_config() -> None:
    """Reset the configuration singleton (useful for testing)."""
    global _config
    _config = None
