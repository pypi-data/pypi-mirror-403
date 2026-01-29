"""Module with TypedDicts using in kwargs."""

from typing import Any

from typing_extensions import TypedDict

from web_sdk.core.fields import AKwarg


class RestFieldsKwargs(TypedDict, total=False):
    """Fields kwargs for request."""

    paths: AKwarg[dict[str, Any] | None]
    """Request path parts for template formatting"""
    body: AKwarg[dict[str, Any] | None]
    """Request body parts"""
    headers: AKwarg[dict[str, Any] | None]
    """Request headers parts"""
    params: AKwarg[dict[str, Any] | None]
    """Request params parts"""
    files: AKwarg[dict[str, Any] | None]
    """Request files parts"""
    cookies: AKwarg[dict[str, str] | None]
    """Request cookies parts"""
