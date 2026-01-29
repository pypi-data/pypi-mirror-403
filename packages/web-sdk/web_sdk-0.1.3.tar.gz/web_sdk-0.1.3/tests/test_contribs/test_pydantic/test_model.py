import pytest
from pydantic import PydanticUserError

from web_sdk.contrib.pydantic.models import ProxyModel, PydanticIgnore, PydanticModel


def test_ignored_types():
    class Foo(PydanticIgnore): ...

    class FooModel(PydanticModel):
        foo = Foo()

    assert isinstance(FooModel().foo, Foo)

    class Bar: ...

    with pytest.raises(PydanticUserError, match="A non-annotated attribute was detected: `bar.*"):
        # noinspection PyUnusedLocal
        class BarModel(PydanticModel):
            bar = Bar()


def test_proxy_model_validate_and_dump():
    attr1_value = 1
    attr2_value = "2"
    attr3_value = 3
    attr3_other_value = 4
    attr4_value = "5"

    class FooModel(ProxyModel):
        attr1: int
        attr2: str = attr2_value

    assert FooModel(attr1=attr1_value) == FooModel(attr1=attr1_value, attr2=attr2_value)
    assert FooModel(attr1=attr1_value) != FooModel(attr1=attr1_value, attr3=attr3_value)

    assert FooModel.model_validate({"attr1": attr1_value, "attr3": attr3_value}) == FooModel(
        attr1=attr1_value, attr3=attr3_value
    )
    assert FooModel.model_validate({"attr1": attr1_value, "attr3": attr3_value}) != FooModel(
        attr1=attr1_value, attr3=attr3_other_value
    )

    assert (
        FooModel.model_validate({"attr1": attr1_value, "attr3": attr3_value}).model_dump()
        == FooModel(attr1=attr1_value, attr3=attr3_value).model_dump()
        == {"attr1": attr1_value, "attr2": attr2_value, "attr3": attr3_value}
    )
    assert (
        FooModel.model_validate({"attr1": attr1_value, "attr3": attr3_value}).model_dump()
        != FooModel(attr1=attr1_value, attr3=attr3_other_value).model_dump()
    )

    assert FooModel(attr1=attr1_value, attr3=attr3_value, attr4=attr4_value).model_dump(exclude={"attr2", "attr3"}) == {
        "attr1": attr1_value,
        "attr4": attr4_value,
    }


def test_proxy_model_original_object():
    attr1_value = 1
    attr2_value = 2
    attr3_value = 3

    class FooModel(ProxyModel):
        attr1: int

    class BarModel(PydanticModel):
        attr1: int = attr1_value
        attr2: int = attr2_value

    bar = BarModel()
    foo = FooModel.model_validate(bar, from_attributes=True)
    assert foo.original_object == bar
    assert foo.attr1 == bar.attr1
    assert foo.attr2 == bar.attr2

    with pytest.raises(AttributeError, match="'BarModel' object has no attribute 'attr3'"):
        assert foo.attr3

    foo.attr3 = attr3_value

    with pytest.raises(AttributeError, match="'BarModel' object has no attribute 'attr3'"):
        assert foo.original_object.attr3  # pyright: ignore [reportAttributeAccessIssue]

    assert foo.attr3 == attr3_value
    assert foo.extra_data["attr3"] == attr3_value
    assert foo.model_dump()["attr3"] == attr3_value
