from typing import TypedDict

from typing_extensions import NotRequired, Required

from web_sdk.utils.typed_dict import dump_kwargs, extract_keys, pop_kwargs


class _FooTypedDict(TypedDict):
    item1: Required[str]
    item2: NotRequired[str]


def test_extract_keys():
    assert extract_keys(_FooTypedDict) == {"item1", "item2"}


def test_dump_kwargs():
    item1_value = 1
    item2_value = 2
    item3_value = 3

    assert dump_kwargs(_FooTypedDict, item1=item1_value, item2=item2_value, item3=item3_value) == {
        "item1": item1_value,
        "item2": item2_value,
    }


def test_pop_kwargs():
    item2_value = 2
    item3_value = 3

    kwargs = {
        "item2": item2_value,
        "item3": item3_value,
    }

    result = pop_kwargs(_FooTypedDict, kwargs)
    assert result == {
        "item2": item2_value,
    }
    assert kwargs == {"item3": item3_value}
