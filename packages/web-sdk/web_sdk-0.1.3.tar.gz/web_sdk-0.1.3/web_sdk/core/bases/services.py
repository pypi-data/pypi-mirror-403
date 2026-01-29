"""Base service module."""

from __future__ import annotations

from typing import Any, cast

from web_sdk.core.interfaces import IService
from web_sdk.types import TExtras, TKwargs


class BaseService(IService[TKwargs, TExtras]):
    """Base service for rest backend."""

    def __init_subclass__(
        cls,
        path: str = "",
        description: str | None = None,
        extras: TExtras | None = None,
        **kwargs: Any,
    ):
        """Build service class for requests."""
        cls.__build_service__(
            path=path,
            description=description,
            kwargs=cast("TKwargs", kwargs),
            extras=extras,
        )

    @classmethod
    def __build_service__(
        cls,
        path: str = "",
        description: str | None = None,
        kwargs: TKwargs | None = None,
        extras: TExtras | None = None,
    ):
        """Build service class.

        Args:
            path: Path part in url
            description: Service description
            kwargs: Make request kwargs
            extras: Extra kwargs
        """
        cls.path = path
        cls.description = description

        cls.kwargs = kwargs or cast("TKwargs", {})
        cls.extras = extras or cast("TExtras", {})
