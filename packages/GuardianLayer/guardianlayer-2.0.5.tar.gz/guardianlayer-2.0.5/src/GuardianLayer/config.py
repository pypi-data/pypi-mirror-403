"""
Configuration management for GuardianLayer
Uses environment variables with sensible defaults
"""

import os
from typing import Optional


class Config:
    """
    Configuration class for GuardianLayer

    All settings can be overridden via environment variables:
    - GUARDIAN_MAX_REPEATS: Maximum allowed repetitions
    - GUARDIAN_CACHE_SIZE: Cache maximum size
    - GUARDIAN_DB_PATH: Database file path
    - GUARDIAN_LOG_LEVEL: Logging level
    - GUARDIAN_FAILURE_THRESHOLD: Circuit breaker failure threshold
    - GUARDIAN_BASE_COOLDOWN: Base cooldown in seconds
    """

    # Loop Detection Settings
    MAX_REPEATS: int = int(os.getenv("GUARDIAN_MAX_REPEATS", "2"))
    MAX_HISTORY: int = int(os.getenv("GUARDIAN_MAX_HISTORY", "10"))

    # Cache Settings
    CACHE_SIZE: int = int(os.getenv("GUARDIAN_CACHE_SIZE", "1000"))
    CACHE_TTL: int = int(os.getenv("GUARDIAN_CACHE_TTL", "3600"))

    # Database Settings
    DB_PATH: str = os.getenv("GUARDIAN_DB_PATH", "guardian.db")
    MEMORY_DB: bool = os.getenv("GUARDIAN_MEMORY_DB", "false").lower() == "true"

    # Circuit Breaker Settings
    FAILURE_THRESHOLD: int = int(os.getenv("GUARDIAN_FAILURE_THRESHOLD", "5"))
    BASE_COOLDOWN: int = int(os.getenv("GUARDIAN_BASE_COOLDOWN", "60"))
    PROBE_LIMIT: int = int(os.getenv("GUARDIAN_PROBE_LIMIT", "3"))

    # Performance Settings
    EST_TOKENS_PER_CALL: int = int(os.getenv("GUARDIAN_EST_TOKENS_PER_CALL", "250"))
    EST_LATENCY_MS: int = int(os.getenv("GUARDIAN_EST_LATENCY_MS", "1000"))
    MAX_CHECKS_PER_SECOND: int = int(os.getenv("GUARDIAN_MAX_CHECKS_PER_SECOND", "100"))

    # Logging Settings
    LOG_LEVEL: str = os.getenv("GUARDIAN_LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("GUARDIAN_LOG_FORMAT", "structured")

    # Advice Generation Settings
    ADVICE_STYLE: str = os.getenv("GUARDIAN_ADVICE_STYLE", "CONCISE")

    # Development/Testing Settings
    DEBUG_MODE: bool = os.getenv("GUARDIAN_DEBUG", "false").lower() == "true"
    METRICS_ENABLED: bool = os.getenv("GUARDIAN_METRICS_ENABLED", "true").lower() == "true"

    @classmethod
    def get_db_path(cls) -> Optional[str]:
        """
        Get the appropriate database path based on configuration

        Returns:
            None for memory database, or file path for persistent storage
        """
        return None if cls.MEMORY_DB else cls.DB_PATH

    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration settings

        Returns:
            True if configuration is valid
        """
        try:
            # Validate numeric values
            if cls.MAX_REPEATS < 1:
                raise ValueError("MAX_REPEATS must be >= 1")
            if cls.CACHE_SIZE < 1:
                raise ValueError("CACHE_SIZE must be >= 1")
            if cls.FAILURE_THRESHOLD < 1:
                raise ValueError("FAILURE_THRESHOLD must be >= 1")
            if cls.BASE_COOLDOWN < 1:
                raise ValueError("BASE_COOLDOWN must be >= 1")

            # Validate log level
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if cls.LOG_LEVEL not in valid_levels:
                raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")

            # Validate advice style
            valid_styles = ["CONCISE", "DETAILED", "MINIMAL"]
            if cls.ADVICE_STYLE not in valid_styles:
                raise ValueError(f"ADVICE_STYLE must be one of: {valid_styles}")

            return True

        except ValueError as e:
            print(f"Configuration validation error: {e}")
            return False

    @classmethod
    def get_config_summary(cls) -> dict:
        """
        Get a summary of current configuration (excluding sensitive data)

        Returns:
            Dictionary with current settings
        """
        return {
            "max_repeats": cls.MAX_REPEATS,
            "max_history": cls.MAX_HISTORY,
            "cache_size": cls.CACHE_SIZE,
            "cache_ttl": cls.CACHE_TTL,
            "db_path": ":memory:" if cls.MEMORY_DB else cls.DB_PATH,
            "memory_db": cls.MEMORY_DB,
            "failure_threshold": cls.FAILURE_THRESHOLD,
            "base_cooldown": cls.BASE_COOLDOWN,
            "probe_limit": cls.PROBE_LIMIT,
            "est_tokens_per_call": cls.EST_TOKENS_PER_CALL,
            "est_latency_ms": cls.EST_LATENCY_MS,
            "max_checks_per_second": cls.MAX_CHECKS_PER_SECOND,
            "log_level": cls.LOG_LEVEL,
            "log_format": cls.LOG_FORMAT,
            "advice_style": cls.ADVICE_STYLE,
            "debug_mode": cls.DEBUG_MODE,
            "metrics_enabled": cls.METRICS_ENABLED,
        }


# Auto-validate on import
if not Config.validate():
    raise RuntimeError("Invalid GuardianLayer configuration detected!")
