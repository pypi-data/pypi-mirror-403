from web_sdk.sdks.rest import Client, Settings

from ..mixins import SessionTestMixin


class _TestClient(Client): ...


class TestRestRequestsClient(SessionTestMixin):
    client_class = _TestClient
    settings_class = Settings
