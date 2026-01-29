"""Module with Client for soap realizations."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeVar

from zeep import Client as ZeepClient
from zeep import Plugin as ZeepPlugin
from zeep import Settings as ZeepSettings

from web_sdk.core.bases import BaseClient
from web_sdk.types import TExtras, TKwargs, TSettings
from web_sdk.utils.contextvar import SimpleContext
from web_sdk.utils.uuid import get_uuid_chars

from . import FileTransport
from .context import SoapContextData
from .methods import SoapMethod
from .schemas import SoapRequestErrorResponse, SoapResponseErrorResponse, SoapRetryErrorResponse

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from zeep.cache import Base as BaseCache

    from .files import SoapFile

_context = SimpleContext[SoapContextData](
    default_factory=lambda: SoapContextData(
        method=None,
        kwargs={},
        extras={},
        # add empty files list
        files=[],
        # make uuid for boundary
        boundary=get_uuid_chars(),
        # make uuid for main part content_id
        content_id=get_uuid_chars(),
    )
)

if TYPE_CHECKING:
    from .settings import BaseSoapSettings

    # noinspection PyTypeHints
    TSettings = TypeVar("TSettings", bound=BaseSoapSettings)


class BaseSoapClient(
    BaseClient[
        SoapMethod[Any, TKwargs, TExtras],  # pyright: ignore [reportInvalidTypeArguments]
        SoapContextData[TKwargs, TExtras],  # pyright: ignore [reportInvalidTypeArguments]
        TSettings,
        TKwargs,
        TExtras,
    ],
    Generic[TSettings, TKwargs, TExtras],
    ABC,
    base=True,
    __context__=_context,
):
    """Base soap client for SDK."""

    __request_error_response__ = SoapRequestErrorResponse
    """Error during make request"""
    __response_error_response__ = SoapResponseErrorResponse
    """Error during prepare response"""
    __retry_error_response__ = SoapRetryErrorResponse
    """Error for max retry count exception"""
    # noinspection PyClassVar
    __transport_class__: ClassVar[type[FileTransport[TKwargs, TExtras]]] = FileTransport  # pyright: ignore [reportGeneralTypeIssues]
    """Transport class for client"""
    __transport_cache_class__: ClassVar[type[BaseCache] | None] = None
    """Transport cache class"""
    __zeep_plugins__: ClassVar[list[ZeepPlugin] | None] = None
    """Zeep client plugins"""
    __zeep_settings__: ClassVar[ZeepSettings | None] = None
    """Zeep client settings"""
    __zeep_wsse__: ClassVar[Any] = None
    """Zeep client wsse"""

    def __get_transport_cache__(self):
        """Return transport cache instance."""
        return self.__transport_cache_class__() if self.__transport_cache_class__ else None

    def __get_transport__(self, session: Any):
        """Return transport instance."""
        if self.__context__ is None:
            raise AttributeError("Attribute __context__ must be set.")

        cache = self.__get_transport_cache__()
        return self.__transport_class__(context=self.__context__, cache=cache, session=session)

    def __get_client__(self, session: Any):
        """Init zeep client."""
        return ZeepClient(
            wsdl=self._settings.url,
            service_name=self._settings.service_name,
            port_name=self._settings.port_name,
            transport=self.__get_transport__(session),
            wsse=self.__zeep_wsse__,
            plugins=self.__zeep_plugins__,
            settings=self.__zeep_settings__,
        )

    def __post_get_session__(self, session: Any):
        """Set zeep client."""
        self._client = self.__get_client__(session)

    @property
    def _client(self) -> ZeepClient:
        if not self._initialized:
            self.__init_session__()

        return self.__client

    @_client.setter
    def _client(self, value: Any):
        self.__client = value

    def _prepare_request_kwargs(self):
        """Extend request kwargs before make request."""
        # pop files from from kwargs
        files_dict: dict[str, SoapFile | Iterable[SoapFile]] = self.kwargs.pop("files", {})  # type: ignore

        # add files to context
        for value in files_dict.values():
            if isinstance(value, (list, tuple)):
                self.context["files"].extend(value)  # pyright: ignore [reportGeneralTypeIssues]
            else:
                self.context["files"].append(value)  # pyright: ignore [reportGeneralTypeIssues]

    def _get_request_method(self) -> Callable[..., Any]:
        """Return request method by SDK Method name."""
        return getattr(self._client.service, self.method.path)

    def _call_request_method(self, request_method: Callable[..., Any]) -> Any:
        """Call soap request method."""
        return request_method(**(self.kwargs.get("body") or {}))
