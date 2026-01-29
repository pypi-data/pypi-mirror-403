"""Module with Client for requests realization."""

from typing import TYPE_CHECKING, Generic, TypeVar

from web_sdk.core.bases import BaseClientService
from web_sdk.core.bases.rest import BaseRestClient
from web_sdk.types import TClient, TExtras

from ..sessions import RequestsSessionMixin
from ..settings import RequestsSettings
from .kwargs import RestRequestsKwargs

if TYPE_CHECKING:
    TSettings = TypeVar("TSettings", bound=RequestsSettings)
else:
    from web_sdk.types import TSettings


class RestRequestsClient(
    RequestsSessionMixin, BaseRestClient[TSettings, RestRequestsKwargs, TExtras], Generic[TSettings, TExtras], base=True
):
    """Base client for requests SDK."""

    __default_settings_class__ = RequestsSettings  # pyright: ignore[reportInvalidTypeForm, reportAssignmentType]
    """Default Client settings class"""


class RestRequestsClientService(BaseClientService[TClient], client=RestRequestsClient):
    """Base service class for requests rest client."""
