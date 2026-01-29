"""Module for working with contextvars."""

from __future__ import annotations

import uuid
from contextvars import ContextVar, copy_context
from copy import deepcopy
from functools import partial, wraps
from typing import TYPE_CHECKING, Generic, Literal, TypeAlias, cast, overload

from typing_extensions import Self

from web_sdk.types import R, T

if TYPE_CHECKING:
    from collections.abc import Callable

AtomicContextModes: TypeAlias = Literal["init", "copy", "share"]


class SimpleContext(Generic[T]):
    """Class for creating a simple context through contextvars.ContextVar."""

    _default: T | None
    _default_factory: Callable[[], T] | None
    _context: ContextVar[T | None]
    _initialized: bool

    def __init__(self, default: T | None = None, default_factory: Callable[[], T] | None = None):
        """Initialize with default values.

        Args:
            default: default value
            default_factory: default value factory
        """
        self._default = default
        self._default_factory = default_factory

        self._context = ContextVar(uuid.uuid4().hex)
        self._initialized = False

    def __init_context__(self) -> None:
        """Initialize context variable value."""
        if self._default_factory:
            self._context.set(self._default_factory())
        else:
            self._context.set(self._default)

        self._initialized = True

    def __copy_from__(self, other: Self):
        """Copy context variable value."""
        self._context.set(deepcopy(other.value))

    @property
    def initialized(self):
        """Return True if the context is initialized."""
        return self._initialized

    @property
    def value(self) -> T:
        """Return context variable value."""
        if not self._initialized:
            self.__init_context__()

        return cast("T", self._context.get())

    @overload
    def atomic_context(
        self,
        function: Callable[..., R],
        mode: AtomicContextModes = "init",
    ) -> Callable[..., R]: ...
    @overload
    def atomic_context(
        self,
        function: None = None,
        mode: AtomicContextModes = "init",
    ) -> Callable[[Callable[..., R]], Callable[..., R]]: ...
    def atomic_context(
        self,
        function: Callable[..., R] | None = None,
        mode: AtomicContextModes = "init",
    ) -> Callable[..., R] | Callable[[Callable[..., R]], Callable[..., R]]:
        """Atomic context during function execution.

        Args:
            function: function for execution in atomic context
            mode: Atomic context mode
                init: The parent context will not change, and the initial value of the context will
                      be the same as when it was first initialized
                copy: The parent context will not change, and the initial value of the context will
                      be the same as the parent
                share: The parent context can change if it is a mutable data type, and the initial
                      value of the context will be the same as the parent

        Returns: passed function or current method

        """
        if not function:
            return partial(self.atomic_context, mode=mode)

        @wraps(function)
        def wrapper(*args, **kwargs) -> R:
            context = copy_context()

            def _function() -> R:
                if mode == "init":
                    self.__init_context__()
                elif mode == "copy":
                    self.__copy_from__(self)
                return function(*args, **kwargs)

            return context.run(_function)

        return wrapper
