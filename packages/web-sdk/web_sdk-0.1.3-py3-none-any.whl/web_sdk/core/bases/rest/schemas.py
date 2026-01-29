"""Module with base classes for methods responses."""

from abc import ABC, abstractmethod
from functools import cached_property
from types import NoneType
from typing import Any, ClassVar, Generic, Literal, cast, overload

from pydantic import HttpUrl, model_validator

from web_sdk.consts import HTTP_500_INTERNAL_SERVER_ERROR
from web_sdk.contrib.pydantic.models import ProxyModel
from web_sdk.core.exceptions import FailureResultSDKException
from web_sdk.types import TData


class _Empty: ...


class BaseRestResponse(ProxyModel, Generic[TData], ABC):
    """Base class for rest methods response."""

    ok: bool
    """True if the response was successful"""

    status_code: int
    """Response status code"""

    @cached_property
    def text(self) -> str:
        """Text of the original response."""
        return self.original_object.text

    @cached_property
    def content(self) -> bytes:
        """Content of the original response."""
        return self.original_object.content

    @property
    @abstractmethod
    def result(self) -> TData:
        """Result of method execution."""
        raise NotImplementedError


class _ResponseProxy:
    """Proxy class for Raw Response."""

    response: Any
    data: Any | None = None

    def __init__(self, response: Any):
        """Set original value to response attribute."""
        self.response = response

    def __getattr__(self, attr):
        """Make ResponseProxy a proxy."""
        return getattr(self.response, attr)


class BaseRestDataResponse(BaseRestResponse[TData], Generic[TData], ABC):
    """Mixin for rest responses which have data."""

    __response_proxy_class__: ClassVar[type[_ResponseProxy]] = _ResponseProxy
    """Proxy class for Response"""

    # noinspection PyTypeHints
    data: TData | type[_Empty] = _Empty

    @property
    def result(self) -> TData:
        """Result of method execution."""
        return cast("TData", self.data)

    @classmethod
    @abstractmethod
    def _extract_data(cls, response: Any) -> Any:
        raise NotImplementedError

    @model_validator(mode="before")
    @classmethod
    def extract_data_validator(cls, response: Any) -> Any:
        """Extract data from response."""
        response_proxy = cls.__response_proxy_class__(response)
        response_proxy.data = cls._extract_data(response)
        return response_proxy


class BaseRestErrorResponse(BaseRestResponse[NoneType]):
    """Error class for rest methods response."""

    ok: bool = False
    status_code: int = HTTP_500_INTERNAL_SERVER_ERROR

    @cached_property
    def text(self):
        """Text of the original response."""
        return ""

    @cached_property
    def content(self) -> bytes:
        """Content of the original response."""
        return b""

    @property
    def result(self) -> None:
        """Empty result of method execution."""
        return None


class RestRequestErrorResponse(BaseRestErrorResponse):
    """Error during make rest request."""


class RestResponseErrorResponse(BaseRestErrorResponse):
    """Error during prepare rest request response."""


class RestRetryErrorResponse(BaseRestErrorResponse):
    """Error for rest max retry count exception."""


class RestRedirectResponse(BaseRestResponse[HttpUrl]):
    """Mixin for rest responses which have redirects."""

    url: HttpUrl

    @property
    def result(self) -> HttpUrl:
        """Result of method execution."""
        return self.url


def is_success(response: BaseRestResponse | None) -> bool:
    """Return True if the rest response was successful."""
    if response is None:
        return False
    if isinstance(response, BaseRestErrorResponse):
        return False
    return response.ok


@overload
def get_res(_response: BaseRestResponse[TData] | None) -> TData: ...
@overload
def get_res(_response: BaseRestResponse[TData] | None, required: Literal[True]) -> TData: ...
@overload
def get_res(_response: BaseRestResponse[TData] | None, required: Literal[False]) -> TData | None: ...
def get_res(_response: BaseRestResponse[TData] | None, required: bool = True) -> TData | None:
    """Return rest request result."""
    if is_success(_response):
        _response = cast("BaseRestResponse[TData]", _response)
        return _response.result

    if not required:
        return None

    raise FailureResultSDKException
