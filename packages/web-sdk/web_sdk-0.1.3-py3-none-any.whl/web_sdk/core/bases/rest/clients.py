"""Module with Client for rest realizations."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, Generic

from web_sdk.core.bases import BaseClient
from web_sdk.core.exceptions import (
    FailureRequestSDKException,
)
from web_sdk.types import TExtras, TKwargs, TSettings
from web_sdk.utils.contextvar import SimpleContext
from web_sdk.utils.url import join_path

from .context import RestContextData
from .methods import RestMethod
from .schemas import (
    RestRequestErrorResponse,
    RestResponseErrorResponse,
    RestRetryErrorResponse,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from .schemas import BaseRestResponse


_context = SimpleContext[RestContextData](
    default_factory=lambda: RestContextData(
        method=None,
        kwargs={},
        extras={},
    )
)


class BaseRestClient(
    BaseClient[
        RestMethod[Any, TKwargs, TExtras],  # pyright: ignore [reportInvalidTypeArguments]
        RestContextData[TKwargs, TExtras],  # pyright: ignore [reportInvalidTypeArguments]
        TSettings,
        TKwargs,
        TExtras,
    ],
    Generic[TSettings, TKwargs, TExtras],
    ABC,
    base=True,
    __context__=_context,
):
    """Base rest client for SDK."""

    __request_error_response__ = RestRequestErrorResponse
    """Error during make request"""
    __response_error_response__ = RestResponseErrorResponse
    """Error during prepare response"""
    __retry_error_response__ = RestRetryErrorResponse
    """Error for max retry count exception"""

    def _prepare_request_kwargs(self):
        """Extend request kwargs before make request."""
        # replace data with body if data is None
        body = self.kwargs.pop("body", {})
        if self.kwargs.get("data") is None:
            self.kwargs["data"] = body  # type: ignore

        # add url from settings.url, method.path and paths
        paths = self.kwargs.pop("paths", None) or {}
        self.kwargs["url"] = join_path(self._settings.url, self.method.path, **paths)  # type: ignore

    def _validate_response(self, response: BaseRestResponse):
        """Validate prepared response.

        Args:
            response: Prepared response

        """
        if not response.ok:
            raise FailureRequestSDKException(path=self.method.name, message=response.text)

    def _get_request_method(self) -> Callable[..., Any]:
        """Return request method by SDK Method HttpMethod."""
        return getattr(self._session, self.method.method.lower())  # pyright: ignore [reportAttributeAccessIssue]

    def _call_request_method(self, request_method: Callable[..., Any]) -> Any:
        """Call rest request method."""
        return request_method(**self.kwargs)
