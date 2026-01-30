"""
Common shared code used by both sync and async implementations.

This package contains configuration, exceptions, logging, utilities,
models, and parameter definitions that are shared across the SDK.
"""

from .config import Config, _default_config, _load_config
from .enums import SessionStatus
from .exceptions import AgentBayError, APIError, AuthenticationError
from .logger import AgentBayLogger, get_logger, log
from .version import __version__

__all__ = [
    "Config",
    "_load_config",
    "_default_config",
    "SessionStatus",
    "AgentBayError",
    "APIError",
    "AuthenticationError",
    "AgentBayLogger",
    "get_logger",
    "log",
    "__version__",
]
