from unittest.mock import MagicMock

import pytest
from pydantic import HttpUrl

from tests.clients.rest import responses as responses
from tests.clients.rest.clients import RestTestClient
from tests.clients.rest.methods import RedirectService
from web_sdk.consts import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from web_sdk.contrib.pydantic.models import ProxyModel
from web_sdk.core.exceptions import (
    FailureRequestSDKException,
)

# noinspection PyProtectedMember
from web_sdk.utils.url import join_path


@pytest.fixture(autouse=True)
def mock_client_get_session(mocker):
    mocker.patch.object(RestTestClient, "__get_session__", return_value=MagicMock())


@pytest.fixture
def client() -> RestTestClient:
    return RestTestClient()


@pytest.mark.parametrize(
    "method,part,response_type",
    [
        ("get", "params", responses.GetResponse),
        ("post", "data", responses.PostResponse),
        ("put", "data", responses.PutResponse),
        ("patch", "data", responses.PatchResponse),
        ("delete", "params", responses.DeleteResponse),
        ("head", "params", responses.HeadResponse),
        ("options", "params", responses.OptionsResponse),
    ],
    ids=[
        "test_get_method",
        "test_post_method",
        "test_put_method",
        "test_patch_method",
        "test_delete_method",
        "test_head_method",
        "test_options_method",
    ],
)
def test_methods(client, method, part, response_type):
    result = getattr(client.methods, method)()
    assert isinstance(result, response_type)

    session_method = getattr(client._session, method)
    assert session_method.call_count == 1

    _, kwargs = session_method.call_args
    assert kwargs[part]["attr"]


@pytest.mark.parametrize(
    "method,path,args",
    [
        ("get", "external", ()),
        ("get_internal", "internal", ()),
        ("get_all", "all", ()),
        ("get_any", "any", ("any",)),
    ],
    ids=[
        "test_path_service_override",
        "test_path_method_override",
        "test_path_decorator_override",
        "test_path_call_override",
    ],
)
def test_path_override(client, method, path, args):
    getattr(client.path_overrides, method)(*args)
    _, kwargs = client._session.get.call_args
    assert kwargs["url"] == join_path(client._settings.url, f"paths_overrides/{path}")


_test_redirect_url = "https://redirect.com"


def _mock_redirect_response(
    mocker,
    url: str = _test_redirect_url,
    text: str = "",
    content: bytes = b"",
    ok: bool = True,
    status_code: int = HTTP_200_OK,
):
    def _new_get_request_method(*_args, **_kwargs):
        return ProxyModel(url=url, text=text, content=content, ok=ok, status_code=status_code)

    return mocker.patch.object(RestTestClient, "_get_request_method", return_value=_new_get_request_method)


def test_redirect(client, mocker):
    _mock_redirect_response(mocker)
    assert client.redirect.get_redirect().result == HttpUrl(_test_redirect_url)


def test_not_ok_response(client, mocker):
    _mock_redirect_response(mocker, ok=False, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

    with pytest.raises(FailureRequestSDKException, match="The response for get_redirect returned with not ok status."):
        assert client.redirect.get_redirect()


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"body": True}, {"data": True}),
        ({"data": True}, {"data": True}),
        ({"body": True, "data": False}, {"data": False}),
    ],
    ids=[
        "prepare_request_kwargs_with_body",
        "prepare_request_kwargs_with_data",
        "prepare_request_kwargs_with_data_and_body",
    ],
)
def test_prepare_request_kwargs(client, kwargs, expected, mocker):
    mocker.patch.object(RestTestClient, "kwargs", new=kwargs)
    mocker.patch.object(RestTestClient, "method", new=RedirectService.get_redirect)
    client._prepare_request_kwargs()
    assert kwargs.pop("url") == join_path(client._settings.url, "redirect")
    assert expected == kwargs
