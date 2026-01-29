from typing import NewType

import pytest

from web_sdk.utils.strings import Strings, _TTypes

Index = NewType("Index", str)
Column = NewType("Column", str)


def test_regular_strings():
    class FooStrings(Strings):
        key1: str
        key2: str

    assert FooStrings.key1 == "key1"
    assert FooStrings.key2 == "key2"
    assert list(FooStrings) == ["key1", "key2"]
    assert list(FooStrings) == FooStrings.__values__


def test_ignored_keys_strings():
    class FooStrings(Strings):
        __types__: _TTypes = (str, Column)

        key1: Column

    assert "__types__" not in FooStrings.__keys__


def test_raise_wrong_type_with_future_annotation_stings():
    with pytest.raises(NameError, match="name 'Index' is not defined"):
        # noinspection PyUnusedLocal
        class FooStrings(Strings):
            index: "Index"


def test_correct_type_with_future_annotation_stings():
    # noinspection PyUnusedLocal
    class FooStrings(Strings, types=(Index,)):
        index: "Index"


def test_no_string_annotations_strings():
    # noinspection PyUnusedLocal
    class FooStrings(Strings):
        index: Index


def test_multiple_types_with_future_annotation_stings():
    # noinspection PyUnusedLocal
    class FooStrings(Strings, types=(Index, Column)):
        key: str
        index: "Index"
        column: "Column"


def test_type_with_custom_logic():
    class StringWithPrefix(str):
        __prefix__: str = "prefix_"

        def __new__(cls, *args, **kwargs):
            instance = super().__new__(cls, *args, **kwargs)
            return cls.__prefix__ + instance

        @property
        def with_prefix(self):
            return f"{self.__prefix__}{self}"

    class FooStrings(Strings, types=(StringWithPrefix,)):
        regular_key: str
        key_with_prefix: StringWithPrefix

    assert FooStrings.regular_key == "regular_key"
    assert FooStrings.key_with_prefix == "prefix_key_with_prefix"
    assert FooStrings.key_with_prefix == StringWithPrefix("key_with_prefix")


def test_atomic_types():
    class FooStrings(Strings, types=(Index, Column)):
        key: str
        index: Index
        column: Column

    class BarStrings(Strings, types=(Column, Index)):
        key: str
        index: Index
        column: Column

    Strings.__types__ = (str,)
    FooStrings.__types__ = (str, Index, Column)
    BarStrings.__types__ = (str, Column, Index)
