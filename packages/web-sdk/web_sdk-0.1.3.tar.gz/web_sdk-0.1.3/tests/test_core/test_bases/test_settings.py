from web_sdk.core.bases import BaseSDKSettings


def test_settings_url():
    assert BaseSDKSettings().url == "https://0.0.0.0"
    assert BaseSDKSettings(protocol="ws").url == "ws://0.0.0.0"
    assert BaseSDKSettings(protocol="ws", host="127.0.0.1").url == "ws://127.0.0.1"
    assert BaseSDKSettings(protocol="ws", host="127.0.0.1", port=3000).url == "ws://127.0.0.1:3000"
    assert BaseSDKSettings(protocol="ws", host="127.0.0.1", port=3000, api_path="api").url == "ws://127.0.0.1:3000/api"
