"""Interfaces for methods."""

from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING, Any, Concatenate, Generic, Protocol

from typing_extensions import overload

from web_sdk.types import P, PMethod, S, TExtras, TKwargs, TResponse

if TYPE_CHECKING:
    from collections.abc import Callable

    from .services import IService


class __OrigClass(Protocol[TResponse]):
    __args__: tuple[type[TResponse]]


class IMethod(Generic[TResponse, TKwargs, TExtras], ABC):
    """Method interface."""

    validator: Callable[[TResponse], Any] | None
    """Custom validator for method"""
    description: str | None
    """Method description"""
    name: str
    """Attr name for from __set_name__"""

    @overload
    def __call__(
        self, function: Callable[P, Any], /, extras: TExtras | None = None, **kwargs: Any
    ) -> Callable[P, TResponse]: ...
    @overload
    def __call__(
        self, function: None = None, /, extras: TExtras | None = None, **kwargs: Any
    ) -> Callable[[Callable[P, Any]], Callable[P, TResponse]]: ...
    @abstractmethod
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

    @abstractmethod
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

    @overload
    def decorate(
        self, function: Callable[P, Any], /, extras: TExtras | None = None, **kwargs: Any
    ) -> Callable[P, TResponse]: ...
    @overload
    def decorate(
        self, function: None = None, /, extras: TExtras | None = None, **kwargs: Any
    ) -> Callable[[Callable[P, Any]], Callable[P, TResponse]]: ...
    @abstractmethod
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

    @property
    @abstractmethod
    def service(self) -> type[IService[TKwargs, TExtras]]:
        """Service class for method."""
        raise NotImplementedError

    @cached_property
    @abstractmethod
    def path(self) -> str:
        """Method path or method name."""
        raise NotImplementedError

    @cached_property
    @abstractmethod
    def kwargs(self) -> TKwargs:
        """Mergeable request kwargs."""
        raise NotImplementedError

    @cached_property
    @abstractmethod
    def extras(self) -> TExtras:
        """Unmergeable request kwargs."""
        raise NotImplementedError

    @cached_property
    @abstractmethod
    def response_type(self) -> type[TResponse]:
        """Response type for method."""
        raise NotImplementedError
