import pytest

from web_sdk.sdks.soap import Client, Settings

from ..mixins import SessionTestMixin


class _TestClient(Client): ...


class TestSoapRequestsClient(SessionTestMixin):
    client_class = _TestClient
    settings_class = Settings

    @pytest.fixture(autouse=True)
    def disable_zeep(self, mocker):
        mocker.patch.object(_TestClient, "__post_get_session__")
