"""Logging utilities.

Note: This module uses Any for kwargs to match the stdlib logging interface signature.
"""
# ruff: noqa: ANN401

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

GenericParameter = ParamSpec("GenericParameter")
GenericResult = TypeVar("GenericResult")

TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


def _trace_method(self: logging.Logger, message: str, *args: object, **kwargs: Any) -> None:
    """Method to add to Logger instances for TRACE level."""
    if self.isEnabledFor(TRACE_LEVEL):
        self.log(TRACE_LEVEL, message, *args, **kwargs)


def install_trace_logger() -> None:
    """Install TRACE level logging dynamically."""
    logging.Logger.trace = _trace_method  # type: ignore[attr-defined]

    def trace_root(message: str, *args: object, **kwargs: Any) -> None:
        logging.getLogger().log(TRACE_LEVEL, message, *args, **kwargs)

    logging.trace = trace_root  # type: ignore[attr-defined]


def log_method(method: Callable[GenericParameter, GenericResult], display_name: str | None = None):  # noqa: ANN201
    """Wrapper to log entry and exit of methods using TRACE level.

    Note: Don't use this on methods with sensitive information as they might get logged too
    """
    display_name = display_name or method.__name__

    @wraps(method)
    def _wrapper(self: Any, *args: Any, **kwargs: Any):  # noqa: ANN202
        self.logger.trace(f"{display_name}() called with {args!r} and {kwargs!r}")  # type: ignore[attr-defined]
        result = method(self, *args, **kwargs)
        self.logger.trace(f"{display_name}() returned {result!r}")  # type: ignore[attr-defined]
        return result

    return _wrapper
