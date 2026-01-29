"""Utilities for TypedDict."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from web_sdk.types import ATypedDict, TTypedDict


def extract_keys(typed_dict_class: type[ATypedDict]) -> frozenset[str]:
    """Get keys from typed dict.

    Args:
        typed_dict_class: TypedDict which keys we need get

    Returns: Frozen set of TypedDict keys

    """
    return typed_dict_class.__required_keys__ | typed_dict_class.__optional_keys__  # type: ignore[attr-defined]


# TODO: maybe need strict mode
def dump_kwargs(typed_dict_class: type[TTypedDict], /, **kwargs: Any) -> TTypedDict:
    """Extract TypedDict items from kwargs.

    Args:
        typed_dict_class: TypedDict which we need get
        **kwargs: Any kwargs

    Returns: TypedDict

    """
    keys = extract_keys(typed_dict_class)
    # noinspection PyArgumentList
    return typed_dict_class(**{key: value for key, value in kwargs.items() if key in keys})


# TODO: maybe need strict mode
def pop_kwargs(typed_dict_class: type[TTypedDict], /, kwargs: MutableMapping) -> TTypedDict:
    """Pop TypedDict items from kwargs.

    Args:
        typed_dict_class: TypedDict which we need get
        kwargs: Any kwargs

    Returns: TypedDict

    """
    data = {}
    for key in extract_keys(typed_dict_class):
        if key in kwargs:
            data[key] = kwargs.pop(key)

    # noinspection PyArgumentList
    return typed_dict_class(**data)
