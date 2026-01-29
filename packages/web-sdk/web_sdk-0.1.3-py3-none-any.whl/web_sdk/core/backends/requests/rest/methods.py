"""Module with Request method."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Concatenate, Generic, final

from typing_extensions import Unpack, overload

from web_sdk.core.bases.rest import RestMethod
from web_sdk.types import P, PMethod, S, TExtras, TResponse

from .kwargs import RestRequestsKwargsWithSettings

if TYPE_CHECKING:
    from collections.abc import Callable

    from web_sdk.enums import HTTPMethod


# noinspection PyMethodOverriding
@final
class RestRequestsMethod(RestMethod[TResponse, RestRequestsKwargsWithSettings, TExtras], Generic[TResponse, TExtras]):
    """Requests REST Method."""

    # we need it here only because Unpack not working with TypeVar
    if TYPE_CHECKING:

        def __init__(
            self,
            path: str = "",
            method: HTTPMethod = HTTPMethod.GET,
            validator: Callable[[TResponse], bool] | None = None,
            description: str | None = None,
            extras: TExtras | None = None,
            **kwargs: Unpack[RestRequestsKwargsWithSettings],
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
            super().__init__(path, method, validator, description, extras, **kwargs)

        @overload
        def __call__(
            self,
            function: Callable[P, Any],
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[RestRequestsKwargsWithSettings],
        ) -> Callable[P, TResponse]: ...
        @overload
        def __call__(
            self,
            function: None = None,
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[RestRequestsKwargsWithSettings],
        ) -> Callable[[Callable[P, Any]], Callable[P, TResponse]]: ...
        def __call__(
            self,
            function: Callable[P, Any] | None = None,
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[RestRequestsKwargsWithSettings],
        ) -> Callable[P, TResponse] | Callable[[Callable[P, Any]], Callable[P, TResponse]]:  # pyright: ignore [reportReturnType]
            """Decorate function with call.

            Args:
                function: Decorate function
                extras: Extra kwargs
                **kwargs: Request kwargs

            Returns: SDK Method

            """

        def from_method(
            self,
            method: Callable[Concatenate[S, P], Any],
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[RestRequestsKwargsWithSettings],
        ) -> PMethod[P, TResponse]:  # pyright: ignore [reportReturnType]
            """Make Method with getting signature from other method.

            Args:
                method: Method for copy signature
                extras: Extra kwargs
                **kwargs: Request kwargs

            Returns: SDK Method

            """

        @overload
        def decorate(
            self,
            function: Callable[P, Any],
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[RestRequestsKwargsWithSettings],
        ) -> Callable[P, TResponse]: ...
        @overload
        def decorate(
            self,
            function: None = None,
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[RestRequestsKwargsWithSettings],
        ) -> Callable[[Callable[P, Any]], Callable[P, TResponse]]: ...
        def decorate(
            self,
            function: Callable[P, Any] | None = None,
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[RestRequestsKwargsWithSettings],  # type: ignore
        ) -> Callable[P, TResponse] | Callable[[Callable[P, Any]], Callable[P, TResponse]]:  # pyright: ignore [reportReturnType]
            """Decorate function.

            Args:
                function: Decorate function
                extras: Extra kwargs
                **kwargs: Request kwargs

            Returns: SDK Method

            """
