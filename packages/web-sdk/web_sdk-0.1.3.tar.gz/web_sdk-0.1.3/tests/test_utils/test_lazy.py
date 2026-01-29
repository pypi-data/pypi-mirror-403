from __future__ import annotations

from dataclasses import dataclass

from web_sdk.utils.lazy import lazy, unwrap_lazy


def test_lazy():
    @dataclass
    class Foo:
        arg1: int
        arg2: int

    _foo: Foo | None = None

    def create_foo(arg1: int, arg2: int) -> Foo:
        nonlocal _foo

        _foo = Foo(arg1=arg1, arg2=arg2)
        return _foo

    arg1_value = 1
    arg2_value = 2

    lazy_foo = lazy(create_foo, arg1_value, arg2=arg2_value)

    assert _foo is None
    assert lazy_foo.arg1 == arg1_value
    assert lazy_foo.arg2 == arg2_value

    assert isinstance(_foo, Foo)
    assert _foo.arg1 == arg1_value
    assert _foo.arg2 == arg2_value
    assert _foo is lazy_foo._lazy_proxy_original_object


def test_unwrap_lazy():
    @dataclass
    class Foo:
        attr: int

    attr_value = 1

    _original_foo: Foo | None = None

    def _get_foo() -> Foo:
        nonlocal _original_foo

        if _original_foo is None:
            _original_foo = Foo(attr=attr_value)

        return _original_foo

    _lazy_foo = lazy(_get_foo)

    assert _lazy_foo.attr == attr_value
    assert unwrap_lazy(_lazy_foo) is _original_foo
    assert unwrap_lazy(_original_foo) is _original_foo
    assert unwrap_lazy(_original_foo) == Foo(attr=attr_value)
