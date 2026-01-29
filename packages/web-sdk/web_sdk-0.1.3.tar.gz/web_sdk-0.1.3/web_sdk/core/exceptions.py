"""Exceptions for backends."""

from web_sdk.utils.exceptions import ExceptionModel


class MaxRetriesSDKException(ExceptionModel):
    """The maximum number of requests retries."""

    __template__ = "The maximum number of requests retries for {path} has been exceeded. {message}"

    path: str = ""
    message: str = ""


class MaxRetriesAfterDisconnectSDKException(MaxRetriesSDKException):
    """The maximum number of requests retries after disconnect."""

    __template__ = "The maximum number of requests retries after disconnect for {path} has been exceeded. {message}"


class FailureRequestSDKException(ExceptionModel):
    """The response returned with not ok status."""

    __template__ = "The response for {path} returned with not ok status. {message}"

    path: str = ""
    message: str = ""


class FailureResultSDKException(ExceptionModel):
    """Failure result exception."""

    __template__ = "The response does not have success result."


class UnexpectedSDKException(ExceptionModel):
    """Unexpected SDK exception."""

    __template__ = "Unexpected SDK exception during {path} request. {message}"

    path: str = ""
    message: str = ""
