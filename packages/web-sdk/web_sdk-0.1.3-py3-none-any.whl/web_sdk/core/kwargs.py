"""Request kwargs module."""

from typing_extensions import TypedDict

from web_sdk.core.fields import ASetting


class RequestSettingsKwargs(TypedDict, total=False):
    """TypedDict for special expected in make_requests kwargs."""

    raise_exceptions: ASetting[bool | None]
    """Raise exceptions during sdk method execution"""
    test_mode: ASetting[bool | None]
    """Is test mode"""
    skip_for_test: ASetting[bool | None]
    """Skip make_request execution for test"""
    fake_for_test: ASetting[bool | None]
    """Fake result for make_request execution for test"""
    max_retry_count: ASetting[int | None]
    """Max retry count"""
    max_retry_count_after_disconnect: ASetting[int | None]
    """Max retry after disconnect count"""
