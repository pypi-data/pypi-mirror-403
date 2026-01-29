import inspect

from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.utils.annotations import signature_from


def test_signature_from():
    class Foo(PydanticModel):
        """Какая-то документация."""

        attr1: int
        attr2: float

    attr_1_value = 1
    attr_2_value = 2.0

    data = {"attr1": attr_1_value, "attr2": attr_2_value}

    @signature_from(Foo, __return__=False)
    def no_return_signature(**kwargs) -> Foo:
        return Foo(**kwargs)

    assert no_return_signature(**data) == Foo(**data)

    @signature_from(no_return_signature, __params__=False)
    def no_params_signature(*, attr1: int, attr2: float):
        return Foo(attr1=attr1, attr2=attr2)

    assert no_params_signature(**data) == Foo(**data)

    @signature_from(lambda: 1, __return__=False, __params__=False)
    def no_return_no_params_signature(*, attr1: int, attr2: float) -> Foo:
        return Foo(attr1=attr1, attr2=attr2)

    assert no_return_no_params_signature(**data) == Foo(**data)

    @signature_from(no_return_no_params_signature)
    def all_signature(**kwargs):
        return Foo(**kwargs)

    assert all_signature(**data) == Foo(**data)

    signature = inspect.Signature(
        [
            inspect.Parameter(name="attr1", kind=inspect.Parameter.KEYWORD_ONLY, annotation=int),
            inspect.Parameter(name="attr2", kind=inspect.Parameter.KEYWORD_ONLY, annotation=float),
        ],
        return_annotation=Foo,
    )

    assert inspect.signature(no_return_signature) == signature
    assert inspect.signature(no_params_signature) == signature
    assert inspect.signature(no_return_no_params_signature) == signature
    assert inspect.signature(all_signature) == signature
