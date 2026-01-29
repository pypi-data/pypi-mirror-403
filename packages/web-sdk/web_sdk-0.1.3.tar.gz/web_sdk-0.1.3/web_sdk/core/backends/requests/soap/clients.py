"""Module with Client for soap realizations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from web_sdk.core.bases import BaseClientService
from web_sdk.core.bases.soap import BaseSoapClient
from web_sdk.types import TClient, TExtras

from ..sessions import RequestsSessionMixin
from .kwargs import SoapRequestsKwargs
from .settings import RequestsSoapSettings

if TYPE_CHECKING:
    TSettings = TypeVar("TSettings", bound=RequestsSoapSettings)
else:
    from web_sdk.types import TSettings


class SoapRequestsClient(  # pyright: ignore [reportIncompatibleVariableOverride]
    RequestsSessionMixin, BaseSoapClient[TSettings, SoapRequestsKwargs, TExtras], Generic[TSettings, TExtras], base=True
):
    """Base soap client for SDK."""

    __default_settings_class__ = RequestsSoapSettings  # pyright: ignore[reportInvalidTypeForm, reportAssignmentType]
    """Default Client settings class"""


class SoapRequestsClientService(BaseClientService[TClient], client=SoapRequestsClient):
    """Base service class for requests soap client."""
