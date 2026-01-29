"""Settings module."""

from __future__ import annotations

from typing import cast

from web_sdk.utils.lazy import lazy

from .base import WebSDKSettings

__all__ = ["settings"]


__settings = None


def __get_default_settings() -> WebSDKSettings:
    return WebSDKSettings()


def __get_settings() -> WebSDKSettings:
    """Return global Web SDK settings."""
    global __settings

    # noinspection PyProtectedMember
    if __settings:
        return __settings  # type: ignore

    __settings = __get_default_settings()
    if _custom_settings := __settings.custom_settings:
        __settings = _custom_settings()

    return cast("WebSDKSettings", __settings)


# noinspection PyRedeclaration
settings = lazy(__get_settings)
