"""Lib enums."""

import logging
from enum import Enum, IntEnum


class TokenType(Enum):
    """Token types."""

    TOKEN = "token"
    BEARER = "Bearer"
    CUSTOM = "custom"


class HTTPMethod(str, Enum):
    """Enumeration of standard HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"


class LogLevel(IntEnum):
    """Log levels."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
