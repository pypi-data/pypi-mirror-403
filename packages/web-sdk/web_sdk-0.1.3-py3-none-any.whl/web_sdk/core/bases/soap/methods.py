"""Module with Request method."""

from __future__ import annotations

from functools import cached_property

from web_sdk.core.bases import BaseMethod
from web_sdk.core.fields import BodyFieldInfo, RequestFieldInfo
from web_sdk.types import TExtras, TKwargs, TResponse


class SoapMethod(BaseMethod[TResponse, TKwargs, TExtras]):
    """Base SOAP method."""

    @cached_property
    def path(self) -> str:
        """Method path."""
        if self.service.path:
            return f"{self.service.path}.{self._path or self.name}"
        return self._path or self.name

    @property
    def _default_field_info(self) -> type[RequestFieldInfo]:
        """Return default RequestFieldInfo."""
        return BodyFieldInfo
