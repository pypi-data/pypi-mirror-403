"""Soap requests objects."""

__all__ = [
    "Settings",
    "Client",
    "ClientService",
    "Service",
    "Method",
    "SoapResponse",
    "SoapFile",
]

from web_sdk.core.backends.requests.soap import (
    SoapRequestsClient as Client,
)
from web_sdk.core.backends.requests.soap import (
    SoapRequestsClientService as ClientService,
)
from web_sdk.core.backends.requests.soap import SoapRequestsMethod as Method
from web_sdk.core.backends.requests.soap import SoapRequestsService as Service
from web_sdk.core.backends.requests.soap.settings import RequestsSoapSettings as Settings
from web_sdk.core.bases.soap import SoapFile, SoapResponse
