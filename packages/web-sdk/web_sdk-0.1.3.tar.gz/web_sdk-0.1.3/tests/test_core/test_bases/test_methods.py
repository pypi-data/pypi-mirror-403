from copy import deepcopy

from typing_extensions import TypedDict

from web_sdk.core.bases import BaseMethod, BaseService
from web_sdk.core.fields import BodyFieldInfo, RequestFieldInfo

# noinspection PyProtectedMember
from web_sdk.types import TResponse
from web_sdk.utils.dicts import merge_dicts
from web_sdk.utils.url import join_path


def test_methods():
    class FooKwargs(TypedDict, total=False):
        item1: int
        item2: int
        item3: dict

    class FooExtras(FooKwargs, total=False):
        extra: bool

    class FooMethod(BaseMethod[TResponse, FooKwargs, FooExtras]):
        @property
        def _default_field_info(self) -> type[RequestFieldInfo]:
            """Return default RequestFieldInfo."""
            return BodyFieldInfo

    class FooResponse: ...

    service_path_value = "/service/path"
    service_description_value = "Service description"
    service_kwargs_value = FooKwargs(
        item1=1,
        item2=2,
        item3={
            "a": 3,
            "b": 4,
        },
    )
    service_extras_value = FooExtras(**deepcopy(service_kwargs_value), extra=True)

    method_path_value = "/method/path"
    method_description_value = "Method description"
    method_kwargs_value = FooKwargs(
        item2=5,
        item3={
            "b": 6,
            "c": 7,
        },
    )
    method_extras_value = FooExtras(**deepcopy(method_kwargs_value), extra=True)

    merged_extras_value = merge_dicts(service_extras_value, method_extras_value)
    merged_kwargs_value = merge_dicts(service_kwargs_value, method_kwargs_value)

    class FooService(
        BaseService[FooKwargs, FooExtras],
        path=service_path_value,
        description=service_description_value,
        extras=service_extras_value,
        **service_kwargs_value,
    ):
        method = FooMethod[FooResponse](
            path=method_path_value,
            description=method_description_value,
            extras=method_extras_value,
            **method_kwargs_value,
        )

    assert FooService.path == service_path_value
    assert FooService.description == service_description_value
    assert FooService.extras == service_extras_value
    assert FooService.kwargs == service_kwargs_value
    assert FooService.method.path == join_path(service_path_value, method_path_value)
    assert FooService.method.description == method_description_value
    assert FooService.method._extras == method_extras_value
    assert FooService.method._kwargs == method_kwargs_value
    assert FooService.method.extras == merged_extras_value
    assert FooService.method.kwargs == merged_kwargs_value
    assert FooService.method.response_type == FooResponse
