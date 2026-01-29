from dataclasses import dataclass

import pytest
from pydantic import HttpUrl

from web_sdk.consts import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from web_sdk.core.bases.rest import (
    BaseRestErrorResponse,
    RestRedirectResponse,
    RestRetryErrorResponse,
    get_res,
    is_success,
)
from web_sdk.core.exceptions import FailureResultSDKException

url_value = HttpUrl("https://example.com")


def test_error_response():
    response = BaseRestErrorResponse()
    assert response.text == ""
    assert response.content == b""
    assert response.result is None


def test_redirect_response():
    @dataclass(kw_only=True)
    class RawResponse:
        ok: bool = True
        status_code: int = HTTP_200_OK
        url: HttpUrl

    raw_response = RawResponse(url=url_value)
    response = RestRedirectResponse.model_validate(raw_response, from_attributes=True)
    assert response.result == url_value


def test_is_success():
    assert is_success(None) is False
    assert is_success(RestRetryErrorResponse()) is False
    assert (
        is_success(
            RestRedirectResponse(
                url=url_value,
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                ok=False,
            )
        )
        is False
    )
    assert (
        is_success(
            RestRedirectResponse(
                url=url_value,
                status_code=HTTP_200_OK,
                ok=True,
            )
        )
        is True
    )


def test_get_res():
    assert (
        get_res(
            RestRedirectResponse(
                url=url_value,
                status_code=HTTP_200_OK,
                ok=True,
            )
        )
        == url_value
    )

    failure_response = RestRedirectResponse(
        url=url_value,
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        ok=False,
    )

    assert get_res(failure_response, required=False) is None

    with pytest.raises(FailureResultSDKException):
        get_res(failure_response)
