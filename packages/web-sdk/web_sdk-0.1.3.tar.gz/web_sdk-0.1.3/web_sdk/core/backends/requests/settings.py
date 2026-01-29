"""Base requests SDK Config module."""

from collections.abc import MutableMapping
from typing import Any

import requests  # optional
import requests.hooks
import requests.models
from pydantic import Field

from web_sdk.core.bases import BaseSDKSettings


class RequestsSettings(BaseSDKSettings):
    """Base requests settings."""

    # Session settings
    headers: MutableMapping[str, str | bytes] = Field(default_factory=dict)
    """Headers"""
    proxies: dict[str, str] = Field(default_factory=dict)
    """Proxies"""
    hooks: dict[str, list] = Field(default_factory=requests.hooks.default_hooks)
    """Hooks"""
    params: dict[str, Any] = Field(default_factory=dict)
    """Parameters"""
    stream: bool = False
    """Enable stream mode"""
    verify: bool = True
    """Enable verification mode"""
    cert: str | tuple[str, str] | None = None
    """Path to certificate file"""
    max_redirects: int = Field(default_factory=lambda: requests.models.DEFAULT_REDIRECT_LIMIT)
    """Max redirects count"""
    cookies: dict[str, str] = Field(default_factory=dict)
    """Cookies"""
