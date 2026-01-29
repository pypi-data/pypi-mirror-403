"""Module with TypedDicts using in kwargs."""

from typing import Any

from requests.auth import AuthBase

from web_sdk.core.bases.rest import RestFieldsKwargs
from web_sdk.core.fields import AKwarg
from web_sdk.core.kwargs import RequestSettingsKwargs


class RestRequestsKwargs(RestFieldsKwargs, total=False):
    """Backend kwargs for rest requests module."""

    proxies: AKwarg[dict[str, str] | None]
    """Request proxies"""
    hooks: AKwarg[dict[str, str] | None]
    """Request hooks"""

    auth: AKwarg[tuple[str, str] | AuthBase | None]
    """Request auth params"""
    timeout: AKwarg[int | tuple[int, int] | None]
    """Request timeout"""
    allow_redirects: AKwarg[bool | None]
    """Allow request redirects"""
    stream: AKwarg[bool]
    """Enable stream mode"""
    verify: AKwarg[bool]
    """Enable verification mode"""
    cert: AKwarg[str | tuple[str, str] | None]
    """Path to certificate file"""

    data: AKwarg[Any | None]
    """Request data"""
    json: AKwarg[str | None]
    """Request json data"""


class RestRequestsKwargsWithSettings(RestRequestsKwargs, RequestSettingsKwargs, total=False):
    """Total request kwargs with settings for rest requests module."""
