import sys

import pytest

from web_sdk.utils.inspect import get_params_with_values


def test_get_params_with_values_minimal_test():
    arg1_value = 1

    # noinspection PyUnusedLocal
    def _function(arg1: int): ...

    assert get_params_with_values(_function, ["arg1"], arg1_value) == {"arg1": arg1_value}
    assert get_params_with_values(_function, ["arg1"], arg1=arg1_value) == {"arg1": arg1_value}

    with pytest.raises(TypeError, match="multiple values for argument 'arg1'"):
        assert get_params_with_values(_function, ["arg1"], arg1_value, arg1=arg1_value)

    with pytest.raises(TypeError, match="got an unexpected keyword argument 'arg2'"):
        assert get_params_with_values(_function, ["arg1"], arg1_value, arg2=arg1_value)

    with pytest.raises(TypeError, match="missing a required argument: 'arg1'"):
        assert get_params_with_values(_function, ["arg1"])

    if sys.version_info < (3, 14):
        with pytest.raises(ValueError, match="'arg2' is not in list"):
            assert get_params_with_values(_function, ["arg2"], arg1_value)
    else:
        with pytest.raises(ValueError, match=r"list.index\(x\): x not in list"):
            assert get_params_with_values(_function, ["arg2"], arg1_value)


class TestGetParamsWithValues:
    positional_only_value = 1
    positional_or_named_required_value = 2
    positional_or_named_with_default_value = 3
    positional_or_named_with_default_other_value = -3
    args_value = (4, 5)
    named_only_required_value = 6
    named_only_with_default_value = 7
    named_only_with_default_other_value = -7
    kwargs_value = {"kwarg1": 8, "kwarg2": 9}

    @staticmethod
    def static_method(
        positional_only: int,
        /,
        positional_or_named_required: int,
        positional_or_named_with_default: int = positional_or_named_with_default_value,
        *__args__: int,
        named_only_required: int,
        named_only_with_default: int = named_only_with_default_value,
        **__kwargs__: int,
    ): ...

    @classmethod
    def class_method(
        cls,
        positional_only: int,
        /,
        positional_or_named_required: int,
        positional_or_named_with_default: int = positional_or_named_with_default_value,
        *__args__: int,
        named_only_required: int,
        named_only_with_default: int = named_only_with_default_value,
        **__kwargs__: int,
    ): ...

    def method(
        self,
        positional_only: int,
        /,
        positional_or_named_required: int,
        positional_or_named_with_default: int = positional_or_named_with_default_value,
        *__args__: int,
        named_only_required: int,
        named_only_with_default: int = named_only_with_default_value,
        **__kwargs__: int,
    ): ...

    @property
    def regular_function(self):
        # noinspection PyUnusedLocal
        def _regular_function(
            positional_only: int,
            /,
            positional_or_named_required: int,
            positional_or_named_with_default: int = self.positional_or_named_with_default_value,
            *__args__: int,
            named_only_required: int,
            named_only_with_default: int = self.named_only_with_default_value,
            **__kwargs__: int,
        ): ...

        return _regular_function

    @pytest.mark.parametrize(
        "params,args,kwargs,result",
        [
            (
                ["positional_only", "positional_or_named_required"],
                (positional_only_value, positional_or_named_required_value),
                {"named_only_required": named_only_required_value},
                {
                    "positional_only": positional_only_value,
                    "positional_or_named_required": positional_or_named_required_value,
                },
            ),
            (
                ["positional_only", "positional_or_named_required"],
                (positional_only_value,),
                {
                    "positional_or_named_required": positional_or_named_required_value,
                    "named_only_required": named_only_required_value,
                },
                {
                    "positional_only": positional_only_value,
                    "positional_or_named_required": positional_or_named_required_value,
                },
            ),
            (
                ["positional_or_named_required", "positional_only"],
                (positional_only_value,),
                {
                    "positional_or_named_required": positional_or_named_required_value,
                    "named_only_required": named_only_required_value,
                },
                {
                    "positional_or_named_required": positional_or_named_required_value,
                    "positional_only": positional_only_value,
                },
            ),
            (
                ["positional_or_named_with_default"],
                (positional_only_value, positional_or_named_required_value),
                {"named_only_required": named_only_required_value},
                {"positional_or_named_with_default": positional_or_named_with_default_value},
            ),
            (
                ["positional_or_named_with_default"],
                (positional_only_value, positional_or_named_required_value),
                {
                    "positional_or_named_with_default": positional_or_named_with_default_other_value,
                    "named_only_required": named_only_required_value,
                },
                {
                    "positional_or_named_with_default": positional_or_named_with_default_other_value,
                },
            ),
            (
                ["named_only_with_default"],
                (positional_only_value, positional_or_named_required_value),
                {
                    "positional_or_named_with_default": positional_or_named_with_default_other_value,
                    "named_only_required": named_only_required_value,
                },
                {"named_only_with_default": named_only_with_default_value},
            ),
            (
                ["__args__"],
                (
                    positional_only_value,
                    positional_or_named_required_value,
                    positional_or_named_with_default_other_value,
                    *args_value,
                ),
                {"named_only_required": named_only_required_value},
                {"__args__": args_value},
            ),
            (
                ["__args__", "named_only_with_default"],
                (
                    positional_only_value,
                    positional_or_named_required_value,
                    positional_or_named_with_default_other_value,
                    *args_value,
                ),
                {
                    "named_only_required": named_only_required_value,
                    "named_only_with_default": named_only_with_default_other_value,
                },
                {"__args__": args_value, "named_only_with_default": named_only_with_default_other_value},
            ),
            (
                ["kwarg1"],
                (
                    positional_only_value,
                    positional_or_named_required_value,
                    positional_or_named_with_default_other_value,
                    *args_value,
                ),
                {
                    "named_only_required": named_only_required_value,
                    "named_only_with_default": named_only_with_default_other_value,
                    **kwargs_value,
                },
                {"kwarg1": kwargs_value["kwarg1"]},
            ),
            (
                ["kwarg1", "kwarg2", "__kwargs__"],
                (
                    positional_only_value,
                    positional_or_named_required_value,
                    positional_or_named_with_default_other_value,
                    *args_value,
                ),
                {
                    "named_only_required": named_only_required_value,
                    "named_only_with_default": named_only_with_default_other_value,
                    **kwargs_value,
                },
                {"kwarg1": kwargs_value["kwarg1"], "kwarg2": kwargs_value["kwarg2"], "__kwargs__": kwargs_value},
            ),
            (
                [
                    "positional_only",
                    "positional_or_named_required",
                    "positional_or_named_with_default",
                    "__args__",
                    "named_only_required",
                    "named_only_with_default",
                    "kwarg1",
                    "kwarg2",
                    "__kwargs__",
                ],
                (
                    positional_only_value,
                    positional_or_named_required_value,
                    positional_or_named_with_default_other_value,
                    *args_value,
                ),
                {
                    "named_only_required": named_only_required_value,
                    "named_only_with_default": named_only_with_default_other_value,
                    **kwargs_value,
                },
                {
                    "positional_only": positional_only_value,
                    "positional_or_named_required": positional_or_named_required_value,
                    "positional_or_named_with_default": positional_or_named_with_default_other_value,
                    "__args__": args_value,
                    "named_only_required": named_only_required_value,
                    "named_only_with_default": named_only_with_default_other_value,
                    "kwarg1": kwargs_value["kwarg1"],
                    "kwarg2": kwargs_value["kwarg2"],
                    "__kwargs__": kwargs_value,
                },
            ),
            (
                [
                    "__kwargs__",
                    "kwarg2",
                    "kwarg1",
                    "named_only_with_default",
                    "named_only_required",
                    "__args__",
                    "positional_or_named_with_default",
                    "positional_or_named_required",
                    "positional_only",
                ],
                (
                    positional_only_value,
                    positional_or_named_required_value,
                    positional_or_named_with_default_other_value,
                    *args_value,
                ),
                {
                    "named_only_required": named_only_required_value,
                    "named_only_with_default": named_only_with_default_other_value,
                    **kwargs_value,
                },
                {
                    "__kwargs__": kwargs_value,
                    "kwarg2": kwargs_value["kwarg2"],
                    "kwarg1": kwargs_value["kwarg1"],
                    "named_only_with_default": named_only_with_default_other_value,
                    "named_only_required": named_only_required_value,
                    "__args__": args_value,
                    "positional_or_named_with_default": positional_or_named_with_default_other_value,
                    "positional_or_named_required": positional_or_named_required_value,
                    "positional_only": positional_only_value,
                },
            ),
            (
                ["__args__", "__kwargs__"],
                (
                    positional_only_value,
                    positional_or_named_required_value,
                    positional_or_named_with_default_other_value,
                ),
                {
                    "named_only_required": named_only_required_value,
                    "named_only_with_default": named_only_with_default_other_value,
                },
                {"__args__": (), "__kwargs__": {}},
            ),
        ],
    )
    def test_get_params_with_values(self, params, args, kwargs, result):
        assert get_params_with_values(self.regular_function, params, *args, **kwargs) == result

        assert get_params_with_values(self.static_method, params, *args, **kwargs) == result
        assert get_params_with_values(self.class_method, params, "cls", *args, **kwargs) == result
        assert get_params_with_values(self.method, params, "self", *args, **kwargs) == result

        assert get_params_with_values(self.__class__.static_method, params, *args, **kwargs) == result
        assert get_params_with_values(self.__class__.class_method, params, "cls", *args, **kwargs) == result
        assert get_params_with_values(self.__class__.method, params, "self", *args, **kwargs) == result
