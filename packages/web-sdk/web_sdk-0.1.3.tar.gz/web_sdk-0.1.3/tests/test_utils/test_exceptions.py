import pytest

from tests.utils import override_settings
from web_sdk.utils.exceptions import ExceptionModel


def test_exception_text():
    class FooException(ExceptionModel):
        __template__ = "Error {attr1} {attr2}"

        attr1: str
        attr2: str

    attr1_value = "foo"
    attr2_value = "bar"

    exc = FooException(attr1=attr1_value, attr2=attr2_value)
    assert exc.text == FooException.__template__.format(attr1=attr1_value, attr2=attr2_value)


def test_exception_raise():
    class FooException(ExceptionModel):
        __template__ = "Error {attr}"

        attr: str

    attr_value = "foo"

    with pytest.raises(FooException, match=FooException.__template__.format(attr=attr_value)):
        raise FooException(attr=attr_value)


def test_exception_no_template():
    with pytest.raises(AttributeError, match="Attribute template is required for class .*"):
        # noinspection PyUnusedLocal
        class FooException(ExceptionModel): ...


def test_exception_localized_text():
    original_template = "Error {attr1} {attr2}."
    translated_template = "Ошибка {attr1} {attr2}."
    untranslatable_template = "Other error"

    def localization_function(text: str) -> str:
        return {original_template: translated_template}.get(text, text)

    with override_settings(
        localize=True,
        localize_function=localization_function,
    ):

        class FooException(ExceptionModel):
            __template__ = original_template

            attr1: str
            attr2: str

        assert FooException.__template__ == translated_template

        class BarException(ExceptionModel):
            __template__ = untranslatable_template

        assert BarException.__template__ == untranslatable_template
