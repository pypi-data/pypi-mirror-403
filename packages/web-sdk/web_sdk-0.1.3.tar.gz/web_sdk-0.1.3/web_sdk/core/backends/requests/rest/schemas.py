"""Schemas for requests backend."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from web_sdk.core.bases.rest import BaseRestDataResponse
from web_sdk.types import TData

if TYPE_CHECKING:
    import requests  # optional

    # noinspection PyUnusedImports
    import xmltodict
else:
    xmltodict = None


def import_xmltodict() -> None:
    """Import xmltodict module or raise ImportError."""
    global xmltodict
    try:
        import xmltodict
    except ImportError as exc:
        raise ImportError("xmltodict is not installed, run `pip install 'web-sdk[xml]'`") from exc


class RestRequestsJsonResponse(BaseRestDataResponse[TData], Generic[TData]):
    """Response with json data."""

    @classmethod
    def _extract_data(cls, response: requests.Response) -> dict | None:
        """Extract data from response."""
        return response.json()


class RestRequestsXmlResponse(BaseRestDataResponse[TData], Generic[TData]):
    """Response with json data."""

    @classmethod
    def _extract_data(cls, response: requests.Response) -> dict | None:
        """Extract data from response."""
        if xmltodict is None:
            import_xmltodict()

        return xmltodict.parse(response.content)  # type: ignore
