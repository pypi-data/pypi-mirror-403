"""Module with Service class for requests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import Unpack

from web_sdk.core.bases import BaseService
from web_sdk.types import TExtras

from .kwargs import RestRequestsKwargsWithSettings


class RestRequestsService(BaseService[RestRequestsKwargsWithSettings, TExtras]):
    """Service class for requests."""

    # we need it here only because Unpack not working with TypeVar
    if TYPE_CHECKING:

        def __init_subclass__(
            cls,
            path: str = "",
            description: str | None = None,
            extras: TExtras | None = None,
            **kwargs: Unpack[RestRequestsKwargsWithSettings],
        ):
            """Build service class for requests."""
            super().__init_subclass__(path, description, extras, **kwargs)
