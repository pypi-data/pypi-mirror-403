"""Module with Request method."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Concatenate, Generic, final

from typing_extensions import Unpack, overload

from web_sdk.core.bases.soap import SoapMethod
from web_sdk.types import P, PMethod, S, TExtras, TResponse

from .kwargs import SoapRequestsKwargsWithSettings

if TYPE_CHECKING:
    from collections.abc import Callable


# noinspection PyMethodOverriding
@final
class SoapRequestsMethod(SoapMethod[TResponse, SoapRequestsKwargsWithSettings, TExtras], Generic[TResponse, TExtras]):
    """Requests REST Method."""

    # we need it here only because Unpack not working with TypeVar
    if TYPE_CHECKING:

        def __init__(
            self,
            path: str = "",
            validator: Callable[[TResponse], bool] | None = None,
            description: str | None = None,
            extras: TExtras | None = None,
            **kwargs: Unpack[SoapRequestsKwargsWithSettings],
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
            super().__init__(path, validator, description, extras, **kwargs)

        @overload
        def __call__(
            self,
            function: Callable[P, Any],
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[SoapRequestsKwargsWithSettings],
        ) -> Callable[P, TResponse]: ...
        @overload
        def __call__(
            self,
            function: None = None,
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[SoapRequestsKwargsWithSettings],
        ) -> Callable[[Callable[P, Any]], Callable[P, TResponse]]: ...
        def __call__(
            self,
            function: Callable[P, Any] | None = None,
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[SoapRequestsKwargsWithSettings],
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
            **kwargs: Unpack[SoapRequestsKwargsWithSettings],
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
            **kwargs: Unpack[SoapRequestsKwargsWithSettings],
        ) -> Callable[P, TResponse]: ...
        @overload
        def decorate(
            self,
            function: None = None,
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[SoapRequestsKwargsWithSettings],
        ) -> Callable[[Callable[P, Any]], Callable[P, TResponse]]: ...
        def decorate(
            self,
            function: Callable[P, Any] | None = None,
            /,
            extras: TExtras | None = None,
            **kwargs: Unpack[SoapRequestsKwargsWithSettings],  # type: ignore
        ) -> Callable[P, TResponse] | Callable[[Callable[P, Any]], Callable[P, TResponse]]:  # pyright: ignore [reportReturnType]
            """Decorate function.

            Args:
                function: Decorate function
                extras: Extra kwargs
                **kwargs: Request kwargs

            Returns: SDK Method

            """
