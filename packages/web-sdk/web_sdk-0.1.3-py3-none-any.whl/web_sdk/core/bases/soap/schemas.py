"""Module with base classes for methods responses."""

from web_sdk.contrib.pydantic.models import PydanticModel


class SoapResponse(PydanticModel):
    """Base class for soap methods response."""


class BaseSoapErrorResponse(SoapResponse):
    """Error class for soap methods response."""


class SoapRequestErrorResponse(BaseSoapErrorResponse):
    """Error during make soap request."""


class SoapResponseErrorResponse(BaseSoapErrorResponse):
    """Error during prepare soap request response."""


class SoapRetryErrorResponse(BaseSoapErrorResponse):
    """Error for soap max retry count exception."""
