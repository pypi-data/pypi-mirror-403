from packaging.version import parse as parse_version

import web_sdk
from web_sdk.version import version_info


def test_version_info():
    version_info_fields = [
        "web_sdk version",
        "python version",
        "platform",
        "related packages",
        "commit",
    ]

    version_info_string = version_info()
    assert all(f"{field}:" in version_info_string for field in version_info_fields)
    assert version_info_string.count("\n") == 4


def test_standard_version():
    v = parse_version(web_sdk.VERSION)
    assert str(v) == web_sdk.VERSION


def test_version_attribute_is_present():
    assert hasattr(web_sdk, "__version__")


def test_version_attribute_is_a_string():
    assert isinstance(web_sdk.__version__, str)
