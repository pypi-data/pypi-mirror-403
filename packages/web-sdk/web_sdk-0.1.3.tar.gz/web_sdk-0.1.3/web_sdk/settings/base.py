"""Module with base global settings for Web SDK."""

from collections.abc import Callable
from typing import Any

from pydantic import ImportString
from pydantic_settings import BaseSettings, SettingsConfigDict


class WebSDKSettings(BaseSettings):
    """Global Web SDK settings."""

    custom_settings: ImportString[type["WebSDKSettings"]] | None = None
    localize: bool = False
    localize_function: ImportString[Callable[[str], Any]] | None = None

    model_config = SettingsConfigDict(
        env_prefix="WEB_SDK_",
    )


class WebSDKTestSettings(WebSDKSettings):
    """Global Web SDK test settings."""

    model_config = SettingsConfigDict(
        env_prefix="TEST_WEB_SDK_",
    )
