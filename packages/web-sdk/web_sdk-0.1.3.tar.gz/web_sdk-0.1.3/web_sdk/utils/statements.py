"""Utilities for statements."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from web_sdk.types import T


def not_none(*args: T | None, default: T = None) -> T:
    """Return first not None or default."""
    for arg in args:
        if arg is not None:
            return arg
    return default


class _Unset: ...


def first(
    iterable: Iterable[T],
    function: Callable[[T], bool] | None = None,
    raise_exception: bool = False,
    default: T | None | type[_Unset] = _Unset,
) -> T | None:
    """Return first or default value from iterable.

    Args:
        iterable: any Iterable
        function: filter function
        raise_exception: raise exception if no element is found
        default: default value

    Returns: first element or default value

    """

    def _first():
        if function:
            yield from filter(function, iterable)
        else:
            yield from iterable
        if not raise_exception:
            if default is _Unset:
                yield None
            yield cast("T | None", default)

    try:
        return next(_first())
    except StopIteration as exc:
        if default is not _Unset:
            return cast("T | None", default)
        raise exc
