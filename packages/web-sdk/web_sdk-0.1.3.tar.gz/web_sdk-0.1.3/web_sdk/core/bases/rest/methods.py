"""Module with Request method."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from web_sdk.core.bases import BaseMethod
from web_sdk.core.fields import RequestFieldInfo
from web_sdk.enums import HTTPMethod
from web_sdk.types import TExtras, TKwargs, TResponse

if TYPE_CHECKING:
    from collections.abc import Callable


class RestMethod(BaseMethod[TResponse, TKwargs, TExtras]):
    """Base REST method."""

    method: HTTPMethod
    """HTTP method"""

    def __init__(
        self,
        path: str = "",
        method: HTTPMethod = HTTPMethod.GET,
        validator: Callable[[TResponse], bool] | None = None,
        description: str | None = None,
        extras: TExtras | None = None,
        **kwargs: Any,
    ):
        """Init Request method.

        Args:
            path: Path part for method
            method: HTTP method
            validator: Custom validator for method
            description: Method description
            extras: Extra kwargs
            **kwargs: Make request kwargs
        """
        super().__init__(path=path, validator=validator, description=description, extras=extras, **kwargs)
        self.method = method

    @property
    def _default_field_info(self) -> type[RequestFieldInfo]:
        """Return default RequestFieldInfo."""
        return RequestFieldInfo.__methods_defaults__[self.method]
