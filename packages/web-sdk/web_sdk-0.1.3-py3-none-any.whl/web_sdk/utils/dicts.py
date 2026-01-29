"""Module with functions for working with dicts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, TypeVar, cast

from web_sdk.types import ATypedDict

_T = TypeVar("_T", ATypedDict, dict[str, Any])


def merge_dicts(
    *dicts: _T,
    copy: bool = True,
) -> _T:
    """Merge multiple dicts into a single dict."""
    result: _T = cast("_T", {})

    for _dict in dicts:
        for key, value in _dict.items():
            if isinstance(value, dict):
                result[key] = merge_dicts(result.get(key, {}), value, copy=False)  # type: ignore
            else:
                result[key] = value

    if copy:
        result = deepcopy(result)

    return result
