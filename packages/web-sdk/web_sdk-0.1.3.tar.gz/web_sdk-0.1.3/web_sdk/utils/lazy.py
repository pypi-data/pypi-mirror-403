"""Utilities for lazy objects loading."""

from collections.abc import Callable
from functools import partial
from typing import Generic, cast

from web_sdk.types import P, R, T


class LazyProxy(Generic[R]):
    """Lazy proxy object for lazy loading."""

    _lazy_proxy_default_factory: Callable[[], R]
    _lazy_proxy_original_object: R | None = None

    def __init__(self, default_factory: Callable[P, R], *args: P.args, **kwargs: P.kwargs):
        """Set default factory for lazy loading."""
        self._lazy_proxy_default_factory = partial(default_factory, *args, **kwargs)
        self._lazy_proxy_original_object = None

    def __setup(self):
        """Instantiate the original object if not already done."""
        if self._lazy_proxy_original_object is None:
            self._lazy_proxy_original_object = self._lazy_proxy_default_factory()

    def __getattr__(self, name):
        """Intercept attribute access and ensure setup."""
        self.__setup()
        return getattr(self._lazy_proxy_original_object, name)


def lazy(default_factory: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
    """Lazy proxy function for correct annotations."""
    return LazyProxy(default_factory, *args, **kwargs)  # type: ignore[return-value]


def unwrap_lazy(lazy_object: LazyProxy | T) -> T:
    """Unwrap lazy object and return it original object."""
    if isinstance(lazy_object, LazyProxy):
        # noinspection PyProtectedMember
        original_object = lazy_object._lazy_proxy_original_object
    else:
        original_object = lazy_object
    return cast("T", original_object)
