from logging import getLogger

import pytest

from tests.clients.base.clients import BaseTestClient
from web_sdk.core.bases.settings import BaseSDKSettings
from web_sdk.core.utils import make_client_factory


def test_make_client_factory():
    client_factory = make_client_factory(BaseTestClient, BaseSDKSettings)

    default_client = client_factory()

    assert default_client is client_factory()

    client_with_other_settings = client_factory(BaseSDKSettings(username="username"))
    assert default_client is not client_with_other_settings
    assert client_with_other_settings._settings.username == "username"
    assert client_with_other_settings is client_factory(BaseSDKSettings(username="username"))

    client_with_other_logger = client_factory(logger=getLogger("__debug__"))
    assert default_client is not client_with_other_logger
    assert client_with_other_logger._logger is getLogger("__debug__")
    assert client_with_other_logger is client_factory(logger=getLogger("__debug__"))


def test_make_client_factory_wrong_client_type():
    with pytest.raises(TypeError, match="Client type must be a subclass of IClient"):
        make_client_factory(object, BaseSDKSettings)

    with pytest.raises(TypeError, match="Settings type must be a subclass of BaseSDKSettings"):
        make_client_factory(BaseTestClient, object)  # type: ignore

    client_factory = make_client_factory(BaseTestClient, BaseSDKSettings)

    with pytest.raises(TypeError, match="Settings must be instance of .*, you passed .*"):
        client_factory(object)  # type: ignore
