"""Base context value type."""

from typing import Any, Generic

from typing_extensions import Required, TypedDict

from web_sdk.types import TExtras, TKwargs, TMethod
from web_sdk.utils.exceptions import ExceptionModel


class ContextData(TypedDict, Generic[TMethod, TKwargs, TExtras], total=False):
    """Request context data."""

    method: Required[TMethod | None]
    """SDK Method"""
    kwargs: Required[TKwargs]
    """Make request kwargs"""
    extras: Required[TExtras]
    """Extra kwargs"""
    raise_exceptions: bool
    """Raise exceptions during execution"""
    test_mode: bool
    """Is test mode"""
    skip_for_test: bool
    """Skip make_request execution for test"""
    fake_for_test: bool
    """Fake result for make_request execution for test"""
    max_retry_count: int
    """Max retry count"""
    max_retry_count_after_disconnect: int
    """Max retry after disconnect count"""
    retry_number: int
    """Current retry number"""
    retry_number_after_disconnect: int
    """Current retry number after disconnect"""
    exc_after_disconnect: ExceptionModel | None
    """Exception after disconnect"""
    custom: Any
    """Any custom user data"""
