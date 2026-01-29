from typing import TypedDict

from web_sdk.core.bases import BaseService


def test_services():
    class FooKwargs(TypedDict):
        item: int

    class FooExtras(TypedDict):
        item: bool

    path_value = "/some/path"
    description_value = "Service description"
    extras_value = FooExtras(item=True)
    kwargs_value = FooKwargs(item=1)

    class FooService(
        BaseService[FooKwargs, FooExtras],
        path=path_value,
        description=description_value,
        extras=extras_value,
        **kwargs_value,
    ): ...

    assert FooService.path == path_value
    assert FooService.description == description_value
    assert FooService.extras == extras_value
    assert FooService.kwargs == kwargs_value
