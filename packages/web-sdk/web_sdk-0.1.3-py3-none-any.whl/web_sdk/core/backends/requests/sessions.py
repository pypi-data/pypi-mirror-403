"""Requests session utils."""

import http.client
from copy import deepcopy

import requests
import urllib3
from requests.cookies import cookiejar_from_dict

from web_sdk.core.exceptions import UnexpectedSDKException

from .settings import RequestsSettings


class RequestsSessionMixin:
    """Mixin for requests session creation."""

    _settings: RequestsSettings

    def __get_session__(self):
        """Init requests.Session."""
        session = requests.Session()
        session.headers = deepcopy(self._settings.headers)
        session.proxies = deepcopy(self._settings.proxies)
        session.hooks = deepcopy(self._settings.hooks)
        session.params = deepcopy(self._settings.params)
        session.cookies = deepcopy(cookiejar_from_dict(self._settings.cookies))
        session.stream = self._settings.stream
        session.verify = self._settings.verify
        session.cert = self._settings.cert
        session.max_redirects = self._settings.max_redirects

        if self._settings.token:
            session.headers["authorization"] = self._authorization_token  # type: ignore
        elif self._settings.username and self._settings.password:
            session.auth = (self._settings.username, self._settings.password)
        if self._settings.api_key:
            session.headers[self._settings.api_key_header] = self._settings.api_key

        return session

    def _check_disconnected_exception(self, exc: UnexpectedSDKException):
        """Raise exception higher if it is not disconnected exception."""
        # here we look only on http.client.RemoteDisconnected exception through "rise new_exc from old_exc" context
        if not isinstance(exc.__context__, requests.exceptions.ConnectionError):
            raise exc
        if not isinstance(exc.__context__.__context__, urllib3.exceptions.ProtocolError):
            raise exc
        if not isinstance(exc.__context__.__context__.__context__, http.client.RemoteDisconnected):
            raise exc
