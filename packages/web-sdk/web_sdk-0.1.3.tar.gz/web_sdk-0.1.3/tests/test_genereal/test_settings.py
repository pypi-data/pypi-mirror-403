# noinspection PyProtectedMember
from web_sdk.settings import __get_settings, settings
from web_sdk.settings.base import WebSDKSettings, WebSDKTestSettings
from web_sdk.utils.lazy import unwrap_lazy


def test_settings():
    assert settings.custom_settings is None
    original_settings = unwrap_lazy(settings)
    assert isinstance(original_settings, WebSDKTestSettings)


def test_get_base_settings(mocker):
    mocker.patch("web_sdk.settings.__settings", new=None)
    mocker.patch(
        "web_sdk.settings.__get_default_settings",
        return_value=WebSDKSettings(custom_settings=None),
    )
    assert unwrap_lazy(__get_settings()).__class__ is WebSDKSettings


def test_get_test_settings():
    assert settings.custom_settings is None
    assert unwrap_lazy(__get_settings()) is unwrap_lazy(settings)
