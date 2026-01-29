"""Client bases."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from logging import Logger, getLogger
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, Generic, cast

from typing_extensions import Self, final

from web_sdk.contrib.pydantic.utils import convert
from web_sdk.core.exceptions import (
    MaxRetriesAfterDisconnectSDKException,
    MaxRetriesSDKException,
    UnexpectedSDKException,
)
from web_sdk.core.interfaces import IClient
from web_sdk.core.kwargs import RequestSettingsKwargs
from web_sdk.enums import LogLevel, TokenType
from web_sdk.types import PLogger, TClient, TContext, TExtras, TKwargs, TMethod, TSettings
from web_sdk.utils.annotations import signature_from
from web_sdk.utils.exceptions import ExceptionModel
from web_sdk.utils.statements import not_none

if TYPE_CHECKING:
    from collections.abc import Callable

    from web_sdk.utils.contextvar import SimpleContext


class BaseClient(IClient[TMethod, TContext, TSettings, TKwargs, TExtras], ABC):
    """Base client for SDK."""

    class __RetryException(Exception):
        """Internal exception for retry requests."""

    # noinspection PyClassVar
    __context__: ClassVar[SimpleContext[TContext] | None] = None  # pyright: ignore [reportGeneralTypeIssues]
    """Context was applied for class"""
    __base_service__: ClassVar[type[BaseClientService]]
    """Base client service class"""
    __services__: ClassVar[dict[str, type[BaseClientService]]]
    """Dict with types of RequestsClientServices"""
    # noinspection PyClassVar
    __default_settings_class__: ClassVar[type[TSettings]]  # pyright: ignore [reportGeneralTypeIssues]
    """Default Client settings class"""
    __default_test_response__: ClassVar[Any] = None
    """Default response during tests run"""
    __default_test_response_factory__: ClassVar[Callable | None] = None
    """Default response factory during tests run"""

    __request_error_response__: ClassVar[type]
    """Error during make request"""
    __response_error_response__: ClassVar[type]
    """Error during prepare response"""
    __retry_error_response__: ClassVar[type]
    """Error for max retry count exception"""

    __expected_exceptions__: ClassVar[tuple[type[Exception], ...]] = (ExceptionModel,)
    """Tuple of expected exceptions during _make_request execution"""

    _settings: TSettings
    """Current instance settings"""
    _logger: PLogger | Logger | None = None
    """Current instance logger"""
    _initialized: bool = False
    """Is current session initialized"""

    def __init_subclass__(cls, base: bool = False, __context__: SimpleContext[TContext] | None = None, **kwargs):
        """Register services in subclass."""
        super().__init_subclass__(**kwargs)

        if __context__:
            cls.__set_context__(__context__)

        if base:
            return

        cls.__validate_subclass__()
        cls.__register_services__()

    def __init__(
        self,
        settings: TSettings | None = None,
        *,
        logger: str | Logger | None = None,
    ):
        """Set settings, logger and services instances.

        Args:
            settings: Settings of client
            logger: logger for errors record
        """
        self._set_settings(settings)
        self._set_logger(logger)
        self._set_services()

    @classmethod
    def __set_context__(cls, context: SimpleContext[TContext]):
        """Set context on make_request function."""
        if cls.__context__:
            raise ValueError("Context already applied in one of base classes")

        cls.__context__ = context
        cls.make_request = signature_from(cls.make_request)(  # pyright: ignore[reportAttributeAccessIssue]
            cls.__context__.atomic_context(cls.make_request, "init")
        )

    @classmethod
    def __register_services__(cls):
        """Register client services to client class."""
        cls.__services__ = {}

        services = cls.__base_service__.__get_registered_subclasses__()

        # noinspection PyTypeChecker
        for _cls in reversed(cls.__mro__):
            for key, value in getattr(_cls, "__annotations__", {}).items():
                if isinstance(value, str) and value in services:
                    cls.__services__[key] = services[value]
                elif isinstance(value, type) and issubclass(value, cls.__base_service__):
                    cls.__services__[key] = value

    @classmethod
    def __validate_subclass__(cls):
        """Validate subclass attributes."""
        if not cls.__context__:
            raise ValueError(
                "Attribute __context__ value must be set. Use __context__, or base arguments in declaration."
            )

        if not hasattr(cls, "__base_service__"):
            raise AttributeError(
                "Attribute __base_service__ is required attribute. Use base = True in declaration, "
                "then declare BaseClientService subclass with current client as value of __client__ in declaration"
            )

        if not hasattr(cls, "__default_settings_class__"):
            raise AttributeError("Attribute __default_settings_class__ is required attribute. Set it as cls attribute.")

    @classmethod
    def build_client(cls, settings: TSettings | None = None, logger: str | Logger | None = None) -> Self:
        """Create client instances for given settings and logger."""
        return cls(settings=settings, logger=logger)

    @abstractmethod
    def __get_session__(self) -> Any:
        """Get session for client instance."""
        raise NotImplementedError

    def __post_get_session__(self, session: Any):
        """Call after session getting."""

    def __init_session__(self):
        """Init session for client instance."""
        self._session = session = self.__get_session__()
        self.__post_get_session__(session)

        self._initialized = True

        if self._settings.need_authentication:
            self._authenticate()

    @property
    def _session(self) -> Any:
        if not self._initialized:
            self.__init_session__()

        return self.__session

    @_session.setter
    def _session(self, value: Any):
        self.__session = value

    @property
    def _authorization_token(self) -> str:
        """Get authorization token from settings."""
        if self._settings.token_type == TokenType.CUSTOM:
            if self._settings.custom_token_type:
                return f"{self._settings.custom_token_type} {self._settings.token}"
        elif self._settings.token_type:
            return f"{self._settings.token_type.value} {self._settings.token}"
        return self._settings.token or ""

    def _set_settings(self, settings: TSettings | None = None):
        """Set settings for client instance."""
        if settings is not None:
            self._settings = settings
        if getattr(self, "_settings", None) is None:
            # noinspection PyTypeChecker
            self._settings = self.__class__.__default_settings_class__()

    def _set_logger(self, logger: Logger | str | None = None):
        """Set logger for client instance."""
        current_logger = None

        if logger is not None:
            if isinstance(logger, str):
                current_logger = getLogger(logger)
            else:
                current_logger = logger

        # use logger from settings if it is specified
        if not current_logger:
            if self._settings.default_logger:
                current_logger = self._settings.default_logger
            elif self._settings.default_logger_name is not None:
                current_logger = getLogger(self._settings.default_logger_name)
            elif self._settings.use_logging_as_default_logger:
                current_logger = logging  # type: ignore[assignment]

        self._logger = cast("PLogger | Logger | None", current_logger)

    def _set_services(self):
        """Set services for client instance."""
        for service_attr, service_type in self.__services__.items():
            service = service_type(self)
            setattr(self, service_attr, service)

    def _authenticate(self):
        """Additional authentication for client instance."""

    def _retry_request(self):
        """Retry request."""
        raise self.__RetryException

    @property
    def _retry_exception(self):
        """Retry request."""
        return self.__RetryException

    def _make_request_error_response(self):
        """Return request error instance."""
        return self.__request_error_response__()

    def _make_response_error_response(self):
        """Return prepare error instance."""
        return self.__response_error_response__()

    def _make_retry_error_response(self):
        """Return prepare error instance."""
        return self.__retry_error_response__()

    def _get_skip_response(self):
        """Extend request kwargs before make request."""
        return None

    def _get_fake_response(self):
        """Extend request kwargs before make request."""
        response_type = self.method.response_type
        if factory := getattr(response_type, "__factory__", None):
            return factory.build()
        if self.__class__.__default_test_response_factory__:
            return self.__class__.__default_test_response_factory__()
        if self.__default_test_response__:
            return self.__default_test_response__
        return None

    def _prepare_request_kwargs(self):
        """Extend request kwargs before make request."""

    def _validate_request_kwargs(self):
        """Validate request kwargs before make request."""

    def _validate_raw_response(self, response: Any):
        """Validate raw response.

        Args:
            response: Raw response

        """

    def _validate_response(self, response: Any):
        """Validate prepared response.

        Args:
            response: Prepared response

        """

    def _method_validate_response(self, response):
        """Validate prepared response with method validator.

        Args:
            response: Prepared response

        """
        if self.method.validator:
            self.method.validator(response)

    def _prepare_response(self, response: Any) -> Any:
        """Prepare raw response.

        Args:
            response: requests.Response

        """
        return convert(self.method.response_type, response, from_attributes=True)

    def _finalize_response(self, response: Any) -> Any:
        """Finalize response after validation.

        Args:
            response: Validated response

        """
        return response

    @abstractmethod
    def _get_request_method(self) -> Callable[..., Any]:
        """Return request method."""

    @abstractmethod
    def _call_request_method(self, request_method: Callable[..., Any]) -> Any:
        """Call request method, getting from _get_request_method."""

    def _check_disconnected_exception(self, exc: UnexpectedSDKException) -> None:
        """Raise exception higher if it is not disconnected exception."""
        raise exc

    def _make_request(self):
        """Make request."""
        raise_exceptions = self.context.get("raise_exceptions", True)
        # make request part
        try:
            # additional preparing request kwargs
            self._prepare_request_kwargs()
            # additional validating request kwargs
            self._validate_request_kwargs()
            # get request method
            request_method = self._get_request_method()
            # call request method
            response = self._call_request_method(request_method)
        # for retry exception raise it higher to make_request method
        except self._retry_exception as exc:
            raise exc
        except self.__expected_exceptions__ as exc:
            if raise_exceptions:
                raise exc
            return self._make_request_error_response()
        # for unexpected exception write log
        except Exception as exc:
            unexpected_error = UnexpectedSDKException()
            self.logging(message=unexpected_error.text, method=self.method, exc=exc)

            # raise exception if specified
            if raise_exceptions:
                raise unexpected_error from exc
            # otherwise return request_error_response instance to determine the error
            return self._make_request_error_response()

        # prepare response part
        try:
            # validate raw response
            self._validate_raw_response(response)
            # prepare raw response
            response = self._prepare_response(response)
            # validate prepared response
            self._validate_response(response)
            self._method_validate_response(response)
            # finalize validated response
            return self._finalize_response(response)
        # for retry exception raise it higher to make_request method
        except self._retry_exception as exc:
            raise exc
        except self.__expected_exceptions__ as exc:
            if raise_exceptions:
                raise exc
            return self._make_response_error_response()
        # for unexpected exception write log
        except Exception as exc:
            unexpected_error = UnexpectedSDKException()
            self.logging(
                message=unexpected_error.text,
                response=response,
                method=self.method,
                exc=exc,
            )

            # raise exception if specified
            if raise_exceptions:
                raise unexpected_error from exc
            # otherwise return response_error_response instance to determine the error
            return self._make_response_error_response()

    @final
    def make_request(
        self,
        method: TMethod,
        kwargs: TKwargs,
        extras: TExtras,
        *,
        raise_exceptions: bool | None = None,  # pyright: ignore [reportRedeclaration]
        test_mode: bool | None = None,  # pyright: ignore [reportRedeclaration]
        skip_for_test: bool | None = None,  # pyright: ignore [reportRedeclaration]
        fake_for_test: bool | None = None,  # pyright: ignore [reportRedeclaration]
        max_retry_count: int | None = None,  # pyright: ignore [reportRedeclaration]
        max_retry_count_after_disconnect: int | None = None,  # pyright: ignore [reportRedeclaration]
        __retry_number: int = 0,
        __retry_number_after_disconnect: int = 0,
        __exc_after_disconnect: ExceptionModel | None = None,
        # To correctly annotate private arguments
        **__kwargs__,
    ) -> Any | None:
        """Entrypoint for make request.

        Args:
            method: SDK Method
            kwargs: Make request kwargs
            extras: Extra kwargs
            raise_exceptions: Raise exceptions during execution
            test_mode: Is test mode
            skip_for_test: Skip make_request execution for test
            fake_for_test: Fake result for make_request execution for test
            max_retry_count: Max retry count
            max_retry_count_after_disconnect: Max retry after disconnect count
            __retry_number: Current retry number
            __retry_number_after_disconnect: Current retry number after disconnect
            __exc_after_disconnect: Exception after disconnect

        Returns: SDK Method response or None

        """
        # get settings kwargs from call or settings
        raise_exceptions: bool = not_none(raise_exceptions, default=self._settings.raise_exceptions)
        test_mode: bool = not_none(test_mode, default=self._settings.test_mode)
        skip_for_test: bool = not_none(skip_for_test, default=self._settings.skip_for_test)
        fake_for_test: bool = not_none(fake_for_test, default=self._settings.fake_for_test)
        max_retry_count: int = not_none(max_retry_count, default=self._settings.max_retry_count)
        max_retry_count_after_disconnect: int = not_none(
            max_retry_count_after_disconnect, default=self._settings.max_retry_count_after_disconnect
        )

        # we record the context for atomic access throughout the execution of a request in custom function
        self.context.update(
            method=method,
            kwargs=kwargs,
            # we ignore it because it is impossible to correctly annotate with generic types.
            extras=extras,  # pyright: ignore [reportArgumentType)]
            test_mode=test_mode,
            skip_for_test=skip_for_test,
            fake_for_test=fake_for_test,
            raise_exceptions=raise_exceptions,
            max_retry_count=max_retry_count,
            max_retry_count_after_disconnect=max_retry_count_after_disconnect,
            retry_number=__retry_number,
            retry_number_after_disconnect=__retry_number_after_disconnect,
            exc_after_disconnect=__exc_after_disconnect,
        )

        # optional skip or fake for tests
        if test_mode:
            if skip_for_test:
                return self._get_skip_response()
            if fake_for_test:
                return self._get_fake_response()

        # max retries control
        if __retry_number > max_retry_count or __retry_number_after_disconnect > max_retry_count_after_disconnect:
            # choose correct exception
            if __exc_after_disconnect:
                exc = MaxRetriesAfterDisconnectSDKException(path=method.name, message=str(__exc_after_disconnect) or "")
            else:
                exc = MaxRetriesSDKException(path=method.name)

            # record exception
            self.logging(message=exc.text, method=method, exc=exc)

            # raise exception if necessary
            if raise_exceptions:
                raise exc
            return self._make_retry_error_response()

        # deep copy kwargs for retry
        kwargs_copy = deepcopy(kwargs)
        extras_copy = deepcopy(extras)
        # write settings kwargs in one dict
        settings = RequestSettingsKwargs(
            raise_exceptions=raise_exceptions,
            test_mode=test_mode,
            skip_for_test=skip_for_test,
            fake_for_test=fake_for_test,
            max_retry_count=max_retry_count,
            max_retry_count_after_disconnect=max_retry_count_after_disconnect,
        )

        try:
            # try to make request
            return self._make_request()
        # try again if RetryRequest was raised
        except self._retry_exception:
            # try to make request
            return self.make_request(
                method=method,
                kwargs=kwargs_copy,
                extras=extras_copy,
                **settings,
                # we increase the counter for the current case
                _BaseClient__retry_number=__retry_number + 1,
                # perhaps you should use _RestClient__retry_number_after_disconnect=0 here,
                # but I think that in this case an uncontrolled request loop may occur
                _BaseClient__retry_number_after_disconnect=__retry_number_after_disconnect,
                # here we do not pass _RestClient__exc_after_disconnect since it should
                # actually be in the context of the SDKMaxRetriesException exception
            )
        # try again when remote disconnect during using session
        except UnexpectedSDKException as exc:
            self._check_disconnected_exception(exc)

            # recreate session instance
            self.__init_session__()

            # make retry with different max retry counter
            return self.make_request(
                method=method,
                kwargs=kwargs_copy,
                extras=extras_copy,
                **settings,
                _BaseClient__retry_number=__retry_number,
                # we increase the counter specifically for the current case
                _BaseClient__retry_number_after_disconnect=__retry_number_after_disconnect + 1,
                # pass exception for case when this is the last attempt of reinit session after disconnect
                _BaseClient__exc_after_disconnect=exc,
            )

    def logging(
        self,
        message: str,
        method: TMethod | None = None,
        level: LogLevel = LogLevel.ERROR,
        logger: Logger | str | None = None,
        exc: Exception | None = None,
        response: Any | None = None,
    ):
        """Record sdk log.

        Args:
            message: Log message
            method: SDK Method
            level: Log level
            logger: Logger for errors record
            exc: Request exception
            response: Request response

        """
        current_logger: PLogger | Logger | None

        # if logger was passed as param use it
        if logger is not None:
            if isinstance(logger, str):
                current_logger = getLogger(logger)
            else:
                current_logger = logger
        # otherwise use logger from instance
        else:
            current_logger = self._logger

        # if logger not specified just return
        if current_logger is None:
            return

        if method:
            # for case when exception raise inside the context of request execution
            current_logger.log(level, f"[{self.__class__.__name__}][{method.name}]: {message}")
        # for case when exception raise outside the context of request execution
        current_logger.log(level, f"[{self.__class__.__name__}]: {message}")

    @property
    def context(self) -> TContext:
        """Return SimpleContext instance value."""
        if self.__context__ is None:
            raise AttributeError("Attribute __context__ must be set.")
        return self.__context__.value

    @property
    def method(self) -> TMethod:
        """Return current context method."""
        if self.context["method"] is None:
            raise ValueError("Request context for is not setting.")
        return self.context["method"]

    @property
    def kwargs(self) -> TKwargs:
        """Return current context kwargs."""
        return self.context["kwargs"]

    @property
    def extras(self) -> TExtras:
        """Return current context extras."""
        # we ignore it because it is impossible to correctly annotate with generic types.
        return self.context["extras"]  # pyright: ignore [reportReturnType]


class BaseClientService(Generic[TClient]):
    """Base service class for rest client."""

    __base_client_service__: ClassVar[type[Self]]
    __registered_subclasses__: ClassVar[dict[str, type[BaseClientService]]] = {}
    """Registered subclasses"""

    client: TClient

    def __init__(self, client: TClient):
        """Set client to service instance."""
        self.client = client

    def __init_subclass__(cls, client: type[TClient] | None = None, **kwargs):
        """Register client service subclass."""
        super().__init_subclass__(**kwargs)

        if client:
            cls.__registered_subclasses__ = {}
            cls.__base_client_service__ = cls
            client.__base_service__ = cls  # pyright: ignore [reportAttributeAccessIssue]
            return

        if cls.__name__ in cls.__registered_subclasses__:
            raise TypeError(
                f"Class name {cls.__name__} already registered in {cls.__base_client_service__}.__registered_subclasses__"
            )
        cls.__registered_subclasses__[cls.__name__] = cls

    @classmethod
    def __get_registered_subclasses__(cls) -> MappingProxyType[str, type[BaseClientService]]:
        """Return registered subclasses."""
        return MappingProxyType(cls.__registered_subclasses__)
