import pytest

from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.contrib.pydantic.utils import convert


class FooModel(PydanticModel):
    attr1: str
    attr2: int


def test_python_convert():
    assert convert(FooModel, {"attr1": "string", "attr2": 2}) == FooModel(attr1="string", attr2=2)
    assert convert(FooModel, '{"attr1": "string", "attr2": 2}', mode="json") == FooModel(attr1="string", attr2=2)
    assert convert(FooModel, {"attr1": "string", "attr2": "2"}, mode="string") == FooModel(attr1="string", attr2=2)

    with pytest.raises(ValueError, match="Unsupported mode: other. Expected one of 'python', 'json', 'string'"):
        convert(FooModel, {}, mode="other")  # type: ignore
