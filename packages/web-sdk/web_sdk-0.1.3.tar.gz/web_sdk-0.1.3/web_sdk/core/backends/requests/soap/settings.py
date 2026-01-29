"""Base requests soap SDK Config module."""

from web_sdk.core.backends.requests.settings import RequestsSettings
from web_sdk.core.bases.soap.settings import BaseSoapSettings


class RequestsSoapSettings(BaseSoapSettings, RequestsSettings):
    """Base requests soap settings."""
