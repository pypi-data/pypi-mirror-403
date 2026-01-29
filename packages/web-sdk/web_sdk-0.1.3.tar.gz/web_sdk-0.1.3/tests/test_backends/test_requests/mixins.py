from http.client import RemoteDisconnected

import pytest
from requests.exceptions import ConnectionError as RequestsConnectionError
from urllib3.exceptions import ProtocolError

from web_sdk.core.backends.requests.settings import RequestsSettings
from web_sdk.core.bases import BaseClient
from web_sdk.core.exceptions import UnexpectedSDKException


def _nested_raise_exceptions(*excs):
    if len(excs) == 1:
        raise excs[0]

    current_exc, *excs = excs

    try:
        _nested_raise_exceptions(*excs)
    except Exception as exc:
        raise current_exc from exc


class SessionTestMixin:
    settings_class: type[RequestsSettings]
    client_class: type[BaseClient]

    def test_client_session(self):
        settings_data = dict(
            headers={"X-Test-Header": "X-Test-Header"},
            proxies={"http": "", "https": ""},
            hooks={"hook1": [], "hook2": []},
            params={"param1": "param1", "param2": "param2"},
            stream=True,
            verify=True,
            cert="/path/to/cert",
            max_redirects=1,
            cookies={"cookie1": "cookie1", "cookie2": "cookie2"},
        )
        settings_with_token = self.settings_class(**settings_data, token="token", api_key="key")  # pyright: ignore [reportArgumentType)]
        settings_with_login = self.settings_class(**settings_data, username="admin", password="password")  # pyright: ignore [reportArgumentType)]
        settings_with_partial_login = self.settings_class(**settings_data, username="admin")  # pyright: ignore [reportArgumentType)]

        client = self.client_class(settings=settings_with_token)
        client.__init_session__()
        session = client._session

        assert session.headers == {
            **settings_with_token.headers,
            "authorization": settings_with_token.token,
            "x-api-key": "key",
        }
        assert session.proxies == settings_with_token.proxies
        assert session.hooks == settings_with_token.hooks
        assert session.params == settings_with_token.params
        assert session.stream == settings_with_token.stream
        assert session.verify == settings_with_token.verify
        assert session.cert == settings_with_token.cert
        assert session.max_redirects == settings_with_token.max_redirects
        assert session.cookies == settings_with_token.cookies

        client_with_login = self.client_class(settings=settings_with_login)
        client_with_login.__init_session__()
        session_with_login = client_with_login._session

        assert session_with_login.headers == settings_with_login.headers
        assert session_with_login.auth == (settings_with_login.username, settings_with_login.password)

        client_with_partial_login = self.client_class(settings=settings_with_partial_login)
        client_with_partial_login.__init_session__()
        session_with_partial_login = client_with_partial_login._session

        assert session_with_partial_login.headers == settings_with_partial_login.headers

    @pytest.mark.parametrize(
        "excs, raised",
        [
            ((UnexpectedSDKException, RequestsConnectionError, ProtocolError, RemoteDisconnected("")), False),
            ((UnexpectedSDKException, RequestsConnectionError, ProtocolError), True),
            ((UnexpectedSDKException, RequestsConnectionError), True),
            ((UnexpectedSDKException,), True),
        ],
    )
    def test_check_disconnected_exception(self, excs: tuple[Exception], raised):
        client = self.client_class()

        try:
            _nested_raise_exceptions(*excs)
        except UnexpectedSDKException as _exc:
            if raised:
                with pytest.raises(UnexpectedSDKException):
                    client._check_disconnected_exception(_exc)
            else:
                assert client._check_disconnected_exception(_exc) is None
