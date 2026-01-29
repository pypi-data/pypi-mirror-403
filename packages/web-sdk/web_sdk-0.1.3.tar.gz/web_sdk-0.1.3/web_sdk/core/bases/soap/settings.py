"""Base settings classes for soap client."""

from web_sdk.core.bases import BaseSDKSettings


class BaseSoapSettings(BaseSDKSettings):
    """Base settings class for soap client."""

    service_name: str | None = None
    """The name of wsdl service."""
    port_name: str | None = None
    """The name of wsdl port."""
