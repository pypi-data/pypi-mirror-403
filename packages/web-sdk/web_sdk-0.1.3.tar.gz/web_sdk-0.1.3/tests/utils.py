from unittest.mock import patch

# noinspection PyProtectedMember
from web_sdk.settings.base import WebSDKSettings
from web_sdk.utils.annotations import signature_from
from web_sdk.utils.lazy import unwrap_lazy


@signature_from(WebSDKSettings, __return__=False)
def override_settings(**kwargs):
    from web_sdk import settings

    if settings.settings.custom_settings:
        """Just for check lazy.__setup was called."""

    original_setting = unwrap_lazy(settings.settings)
    kwargs = {**original_setting.model_dump(), **kwargs}
    # noinspection PyProtectedMember
    settings = original_setting.__class__(**kwargs)  # type: ignore
    return patch("web_sdk.settings.settings._lazy_proxy_original_object", new=settings)
