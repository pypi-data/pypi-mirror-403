"""Base Strings class."""

from __future__ import annotations

import inspect
from abc import ABCMeta
from types import FunctionType
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Generator

_TTypes: TypeAlias = tuple[FunctionType | type, ...]


class StringsMeta(ABCMeta):
    """Metaclass for Strings."""

    __ignored_keys__: ClassVar[tuple[str, ...]] = (
        "__keys__",
        "__types__",
        "__ignored_keys__",
        "__literal_annotations__",
    )
    """Ignored keys for correct values creation."""
    __keys__: tuple[str, ...] = ()

    """Keys of annotated attrs."""
    __types__: _TTypes = (str,)
    """Extra types for using in values creation"""

    def __new__(mcs, name: str, bases: tuple, attrs: dict[str, Any], types: _TTypes = ()) -> type[Strings]:
        """Class object creating.

        Args:
            name: Class name
            bases: Tuple of bases classes or functions
            attrs: Class attributes
            types: Extra types for using in values creation
        """
        cls: type[Strings] = super().__new__(mcs, name, bases, attrs)  # type: ignore

        cls.__types__ = (*cls.__types__, *types)

        __keys__ = list(cls.__keys__)

        # create namespace from __types__
        local_namespace = {_type.__name__: _type for _type in cls.__types__}

        # iterate by annotations
        for key, annotation in inspect.get_annotations(cls).items():
            if key in mcs.__ignored_keys__:
                continue

            __keys__.append(key)

            # if we have string annotations (for example during __future__.annotations using)
            if isinstance(annotation, str):
                # execute string annotation for getting real implementation
                annotation = eval(annotation, local_namespace)
            # convert keys to needed types and set values

            value = annotation(key)
            setattr(cls, key, value)

        cls.__keys__ = tuple(__keys__)

        return cls

    def __iter__(cls) -> Generator[Any]:
        """Iterate over keys."""
        for key in cls.__keys__:
            yield getattr(cls, key)

    @property
    def __values__(cls):
        """Return values list."""
        return list(cls)


class Strings(metaclass=StringsMeta):
    """Class where values equal names of annotated attrs."""
