"""Models for the configuration of the logging module"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

LogLevel = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class FormatterConfig(BaseModel):
    """Formatter configuration."""

    format: str
    datefmt: str | None = None


class HandlerConfig(BaseModel):
    """Handler configuration."""

    class_: str = Field(..., alias="class")
    level: LogLevel | None
    formatter: str | None
    filename: str | None


class LoggerConfig(BaseModel):
    """Logger configuration."""

    level: LogLevel | None
    handlers: list[str] | None


class LoggingConfig(BaseModel):
    """Logging configuration. Allows for extra fields but validates the most common fields."""

    version: int = 1
    disable_existing_loggers: bool
    formatters: dict[str, FormatterConfig] | None
    handlers: dict[str, HandlerConfig] | None
    loggers: dict[str, LoggerConfig] | None
    root: LoggerConfig | None

    model_config = {"extra": "allow"}

    @classmethod
    @field_validator("version")
    def check_version(cls, v: int) -> int:
        """Ensure version is always 1."""
        if v != 1:
            raise ValueError("Logging config version must be 1")
        return v
