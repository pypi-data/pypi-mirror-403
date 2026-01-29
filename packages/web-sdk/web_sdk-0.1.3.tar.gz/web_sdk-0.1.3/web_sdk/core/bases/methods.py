"""Base SDK method module."""

from __future__ import annotations

from abc import abstractmethod
from functools import cached_property, partial, wraps
from inspect import unwrap
from typing import TYPE_CHECKING, Any, Concatenate, Protocol, cast

from typing_extensions import overload

from web_sdk.core.fields.parts import RequestParts
from web_sdk.core.interfaces import IMethod
from web_sdk.types import P, PMethod, S, TExtras, TKwargs, TResponse
from web_sdk.utils.dicts import merge_dicts
from web_sdk.utils.url import join_path

if TYPE_CHECKING:
    from collections.abc import Callable

    from web_sdk.core.bases import BaseService
    from web_sdk.core.fields import RequestFieldInfo


class _POrigClass(Protocol[TResponse]):
    __args__: tuple[type[TResponse]]


class BaseMethod(IMethod[TResponse, TKwargs, TExtras]):
    """Base SDK method."""

    __orig_class__: _POrigClass[TResponse]
    __request_parts__: type[RequestParts[TKwargs, TExtras]] = RequestParts
    """Request parts class for method"""

    _path: str
    """Path part for method or method name"""
    _kwargs: TKwargs
    """Make request kwargs"""
    _extras: TExtras
    """Extra kwargs"""
    _service: type[BaseService[TKwargs, TExtras]]
    """Service class for access to service level kwargs"""

    description: str | None
    """Method description"""
    validator: Callable[[TResponse], Any] | None
    """Custom validator for method"""

    def __init__(
        self,
        path: str = "",
        validator: Callable[[TResponse], bool] | None = None,
        description: str | None = None,
        extras: TExtras | None = None,
        **kwargs: Any,
    ):
        """Init Request method.

        Args:
            path: Path part for method
            validator: Custom validator for method
            description: Method description
            extras: Extra kwargs
            **kwargs: Make request kwargs
        """
        self._path = path
        self._kwargs = cast("TKwargs", kwargs or {})
        self._extras = extras or cast("TExtras", {})

        self.validator = validator
        self.description = description

    def __set_name__(self, owner: type[BaseService[TKwargs, TExtras]], name: str):
        """Set service class to method attribute."""
        self._service = owner
        self.name = name

    @overload
    def __call__(
        self, function: Callable[P, Any], /, extras: TExtras | None = None, **kwargs: Any
    ) -> Callable[P, TResponse]: ...
    @overload
    def __call__(
        self, function: None = None, /, extras: TExtras | None = None, **kwargs: Any
    ) -> Callable[[Callable[P, Any]], Callable[P, TResponse]]: ...
    def __call__(
        self, function: Callable[P, Any] | None = None, /, extras: TExtras | None = None, **kwargs: Any
    ) -> Callable[P, TResponse] | Callable[[Callable[P, Any]], Callable[P, TResponse]]:
        """Decorate function with call.

        Args:
            function: Decorate function
            extras: Extra kwargs
            **kwargs: Request kwargs

        Returns: SDK Method

        """
        return self.decorate(function, extras=extras, **kwargs)

    @property
    @abstractmethod
    def _default_field_info(self) -> type[RequestFieldInfo]:
        """Return default RequestFieldInfo."""

    def _decorate(self, function: Callable[P, Any], /, kwargs: TKwargs, extras: TExtras) -> Callable[P, TResponse]:
        """Decorate function.

        Args:
            function: Decorated function
            kwargs: Make request kwargs
            extras: Extra kwargs

        Returns: SDK Method

        """
        # merge method kwargs with method call kwargs
        method_kwargs = merge_dicts(self.kwargs, kwargs)
        method_extras = merge_dicts(self.extras, extras)

        # set request parts by function signature
        request_parts = self.__request_parts__.get_request_parts(function, self._default_field_info)

        @wraps(function)
        def wrapper(_self, *_args, **_kwargs):
            """Wrapper for SDK Method.

            Args:
                _self: RequestsClientService instance
                *_args: function args
                **_kwargs: function kwargs

            Returns: SDK Method ReturnType

            """
            # get request parts set during _decorate execution
            request_parts_dump = request_parts.dump_request_parts("self", *_args, **_kwargs)
            # make request
            return _self.client.make_request(
                method=self,
                kwargs=merge_dicts(method_kwargs, request_parts_dump["kwargs"]),
                extras=merge_dicts(method_extras, request_parts_dump["extras"]),
                **request_parts_dump["settings"],
            )

        return wrapper

    def from_method(
        self, method: Callable[Concatenate[S, P], Any], /, extras: TExtras | None = None, **kwargs: Any
    ) -> PMethod[P, TResponse]:
        """Make Method with getting signature from other method.

        Args:
            method: Method for copy signature
            extras: Extra kwargs
            **kwargs: Request kwargs

        Returns: SDK Method

        """
        return self.decorate(unwrap(method), extras=extras, **kwargs)

    @overload
    def decorate(
        self, function: Callable[P, Any], /, extras: TExtras | None = None, **kwargs: Any
    ) -> Callable[P, TResponse]: ...
    @overload
    def decorate(
        self, function: None = None, /, extras: TExtras | None = None, **kwargs: Any
    ) -> Callable[[Callable[P, Any]], Callable[P, TResponse]]: ...
    def decorate(
        self,
        function: Callable[P, Any] | None = None,
        /,
        extras: TExtras | None = None,
        **kwargs: Any,  # pyright: ignore [reportRedeclaration]
    ) -> Callable[P, TResponse] | Callable[[Callable[P, Any]], Callable[P, TResponse]]:
        """Decorate function.

        Args:
            function: Decorate function
            extras: Extra kwargs
            **kwargs: Request kwargs

        Returns: SDK Method

        """
        kwargs: TKwargs = cast("TKwargs", kwargs)
        extras = cast("TExtras", extras or {})

        if function is None:
            return partial(self._decorate, kwargs=kwargs, extras=extras)
        return self._decorate(function, kwargs=kwargs, extras=extras)

    @property
    def service(self) -> type[BaseService[TKwargs, TExtras]]:
        """Service class for method."""
        return self._service

    @cached_property
    def path(self) -> str:
        """Method path."""
        return join_path(self.service.path, self._path)

    @cached_property
    def kwargs(self) -> TKwargs:
        """Mergeable request kwargs."""
        return merge_dicts(self.service.kwargs, self._kwargs)  # pyright: ignore [reportGeneralTypeIssues]

    @cached_property
    def extras(self) -> TExtras:
        """Unmergeable request kwargs."""
        return merge_dicts(self.service.extras, self._extras)  # pyright: ignore [reportGeneralTypeIssues]

    @cached_property
    def response_type(self) -> type[TResponse]:
        """Response type for method."""
        return self.__orig_class__.__args__[0]
