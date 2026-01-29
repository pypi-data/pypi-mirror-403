"""Module with TypedDicts using in kwargs."""

from web_sdk.core.bases.soap import SoapFieldsKwargs
from web_sdk.core.kwargs import RequestSettingsKwargs


class SoapRequestsKwargs(SoapFieldsKwargs, total=False):
    """Backend kwargs for soap requests module."""


class SoapRequestsKwargsWithSettings(SoapRequestsKwargs, RequestSettingsKwargs, total=False):
    """Total request kwargs with settings."""
