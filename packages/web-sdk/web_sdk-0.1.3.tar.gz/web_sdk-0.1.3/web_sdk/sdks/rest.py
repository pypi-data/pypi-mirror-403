"""Rest requests objects."""

__all__ = [
    "Settings",
    "Client",
    "ClientService",
    "Service",
    "Method",
    "JsonResponse",
    "XmlResponse",
    "is_success",
    "get_res",
]

from web_sdk.core.backends.requests.rest import RestRequestsClient as Client
from web_sdk.core.backends.requests.rest import RestRequestsClientService as ClientService
from web_sdk.core.backends.requests.rest import RestRequestsJsonResponse as JsonResponse
from web_sdk.core.backends.requests.rest import RestRequestsMethod as Method
from web_sdk.core.backends.requests.rest import RestRequestsService as Service
from web_sdk.core.backends.requests.rest import RestRequestsXmlResponse as XmlResponse
from web_sdk.core.backends.requests.settings import RequestsSettings as Settings
from web_sdk.core.bases.rest import get_res, is_success
