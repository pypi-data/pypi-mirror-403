"""Client interfaces."""

from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Generic

from typing_extensions import Self

from web_sdk.enums import LogLevel
from web_sdk.types import TContext, TExtras, TKwargs, TMethod, TSettings
from web_sdk.utils.exceptions import ExceptionModel


class IClient(Generic[TMethod, TContext, TSettings, TKwargs, TExtras], ABC):
    """Client interface."""

    @classmethod
    @abstractmethod
    def build_client(cls, settings: TSettings | None = None, logger: str | Logger | None = None) -> Self:
        """Create client instances for given settings and logger."""

    @abstractmethod
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

    @abstractmethod
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
    ) -> Any:
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

        Returns: SDK Method return_type or None

        """

    @property
    @abstractmethod
    def context(self) -> TContext:
        """Return context value from context var isolated in make_request execution."""
