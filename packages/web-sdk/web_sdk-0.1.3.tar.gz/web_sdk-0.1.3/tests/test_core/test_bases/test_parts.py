from typing import Annotated

import pytest
from typing_extensions import Unpack

from web_sdk.core.fields import AParam, APath, Param, ParamFieldInfo, Path, PathFieldInfo
from web_sdk.core.fields.parts import RequestParts

# noinspection PyProtectedMember
from web_sdk.types import PartsNames


def test_add_param():
    request_parts = RequestParts.get_request_parts(lambda: None, ParamFieldInfo)
    request_parts.add_param("param1", ParamFieldInfo())

    with pytest.raises(ValueError, match="Duplicate param name: param1"):
        request_parts.add_param("param1", ParamFieldInfo())

    with pytest.raises(ValueError, match="Unsupported field type: <class 'object'>"):
        request_parts.add_param("param2", object())  # type: ignore


def test_skip_param():
    class RequestPartsWithSkip(RequestParts):
        def _skip_part(self, part_name: PartsNames):
            if part_name == "paths":
                return True
            return False

    # noinspection PyUnusedLocal
    def foo(path: APath[bool], param: AParam[bool]): ...

    request_parts = RequestParts.get_request_parts(foo, ParamFieldInfo)
    request_parts_with_skip = RequestPartsWithSkip.get_request_parts(foo, ParamFieldInfo)

    assert request_parts.dump_request_parts(path=True, param=True)["kwargs"] == {
        "paths": {"path": True},
        "params": {"param": True},
    }
    assert request_parts_with_skip.dump_request_parts(path=True, param=True)["kwargs"] == {
        "params": {"param": True},
    }


def test_get_request_parts_with_unexpected_metadata():
    # noinspection PyUnusedLocal
    def foo(param: Annotated[bool, object]): ...

    request_parts = RequestParts.get_request_parts(foo, ParamFieldInfo)

    assert request_parts.dump_request_parts(param=True)["kwargs"]["params"] == {
        "param": True,
    }


def test_get_field_info():
    path = Path()
    param = Param()

    assert RequestParts.get_field_info(path) == path
    assert RequestParts.get_field_info(param, path) == param
    assert isinstance(RequestParts.get_field_info(Path), PathFieldInfo)
    assert isinstance(RequestParts.get_field_info(Param, Path), ParamFieldInfo)
    assert RequestParts.get_field_info(lambda: None) is None  # type: ignore


def test_get_fields_from_var_keyword_param_errors():
    # noinspection PyUnusedLocal
    def no_annotation(**kwargs): ...

    with pytest.raises(
        TypeError, match="Annotation for var keyword 'kwargs' must be unpack with typing_extensions.TypedDict argument"
    ):
        RequestParts.get_request_parts(no_annotation, ParamFieldInfo)

    # noinspection PyUnusedLocal
    def no_argument(**kwargs: Unpack): ...  # type: ignore

    with pytest.raises(
        TypeError, match="Annotation for var keyword 'kwargs' must be unpack with typing_extensions.TypedDict argument"
    ):
        RequestParts.get_request_parts(no_argument, ParamFieldInfo)

    # noinspection PyUnusedLocal
    def foo3(**kwargs: Unpack[type]): ...  # type: ignore

    with pytest.raises(TypeError, match="Arg of var keyword 'kwargs' must be typing_extensions.TypedDict"):
        RequestParts.get_request_parts(foo3, ParamFieldInfo)
