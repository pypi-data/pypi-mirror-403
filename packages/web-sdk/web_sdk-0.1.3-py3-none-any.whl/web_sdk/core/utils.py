"""Core utils for SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

from web_sdk.core.bases import BaseSDKSettings
from web_sdk.core.interfaces.clients import IClient

if TYPE_CHECKING:
    from logging import Logger

    from web_sdk.types import TClient, TSettings


def make_client_factory(client_type: type[TClient], settings_type: type[TSettings]):
    """Make a client factory function for clients.

    Client instance with certain settings and logger create only once. Next, the cached instance is used.

    Args:
        client_type: Client type
        settings_type: Client settings type

    Returns: client factory function

    """
    if not issubclass(client_type, IClient):
        raise TypeError("Client type must be a subclass of IClient")
    if not issubclass(settings_type, BaseSDKSettings):
        raise TypeError("Settings type must be a subclass of BaseSDKSettings")

    _clients: dict[tuple[int, int], TClient] = {}

    def _get_client(settings: TSettings | None = None, logger: str | Logger | None = None) -> TClient:
        if settings and not isinstance(settings, settings_type):
            raise TypeError(f"Settings must be instance of {settings_type}, you passed {settings}")

        _key = (hash(settings), hash(logger))

        if _key in _clients:
            return _clients[_key]

        client = client_type.build_client(settings, logger=logger)
        _clients[_key] = client  # type: ignore
        return client  # type: ignore

    return _get_client
