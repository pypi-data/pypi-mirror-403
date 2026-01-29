import pytest

from web_sdk.core.fields import Path, RequestFieldInfo
from web_sdk.enums import HTTPMethod


def test_request_field_wrong_validation_alias():
    with pytest.raises(
        TypeError, match="Invalid `validation_alias` type. it should be `str`, `AliasChoices`, or `AliasPath`"
    ):
        Path(validation_alias=object)  # type: ignore


def test_request_field_info_no_part_name():
    with pytest.raises(AttributeError, match="Field `part_name` is not defined for .*"):
        # noinspection PyUnusedLocal
        class FooFieldInfo(RequestFieldInfo): ...


def test_request_field_info_override_prats_mapping(mocker):
    mocker.patch.object(RequestFieldInfo, "__parts_mapping__", new={"paths": None})

    _part_name = "paths"
    with pytest.warns(UserWarning, match=f".* subclass for part {_part_name} already exists.*"):
        # noinspection PyUnusedLocal
        class FooFieldInfo(RequestFieldInfo):
            part_name = _part_name


def test_request_field_info_override_methods_default(mocker):
    mocker.patch.object(RequestFieldInfo, "__parts_mapping__")
    mocker.patch.object(RequestFieldInfo, "__methods_defaults__", new={HTTPMethod.GET: None})

    method = HTTPMethod.GET
    with pytest.warns(UserWarning, match=f"Subclass .* specifies {method} in __default_for_methods__.*"):
        # noinspection PyUnusedLocal
        class FooFieldInfo(RequestFieldInfo):
            part_name = "foo"
            default_for_methods = (method,)
