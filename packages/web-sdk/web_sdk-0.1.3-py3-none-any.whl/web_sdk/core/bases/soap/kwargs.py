"""Module with TypedDicts using in kwargs."""

from typing import Any

from typing_extensions import TypedDict

from web_sdk.core.fields import AKwarg


class SoapFieldsKwargs(TypedDict, total=False):
    """Fields kwargs for request."""

    body: AKwarg[dict[str, Any] | None]
    """Request body parts"""
    files: AKwarg[dict[str, Any] | None]
    """Request files parts"""
