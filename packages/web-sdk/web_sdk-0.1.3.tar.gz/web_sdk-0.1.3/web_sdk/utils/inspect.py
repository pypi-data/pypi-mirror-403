"""Inspect utils module."""

from __future__ import annotations

import inspect
from types import MethodType
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


class _DoesNotExists: ...


class _Kwargs: ...


class _Args: ...


def get_params_values(
    _function: Callable,
    _params: Sequence[str],
    *args,
    __mark_params_errors__: bool = False,
    **kwargs,
) -> tuple:
    """Get bind values of certain parameters.

    Args:
        _function: Function
        _params: Params for values getting
        *args: Function arguments
        __mark_params_errors__: Mark as _DoesNotExists if param not in signature and passed kwargs
        **kwargs: Function keyword arguments

    Returns: Tuple of params values

    """
    result = []
    # get original function
    _function = inspect.unwrap(_function)

    # get original signature
    signature = inspect.signature(_function)

    # remove first arg if working with MethodType for correct signature.bind execution
    if issubclass(type(_function), MethodType) and args:
        _, *args_for_bind = args
    else:
        args_for_bind = args

    # check that the arguments match the signature
    signature.bind(*args_for_bind, **kwargs)

    # get full function args specification
    spec = inspect.getfullargspec(_function)

    # get special params
    kwargs_param = spec.varkw
    args_param = spec.varargs

    need_args = False
    need_kwargs = False

    # iter by params
    for param in _params:
        # if param in kwargs add to result
        if param in kwargs:
            result.append(kwargs[param])
        # if param key value only param has default add default to results
        elif spec.kwonlydefaults and param in spec.kwonlydefaults:
            result.append(spec.kwonlydefaults[param])
        elif param == args_param:
            need_args = True
            result.append(_Args)
        elif param == kwargs_param:
            need_kwargs = True
            result.append(_Kwargs)
        else:
            # mark as _DoesNotExists if param not in signature and passed kwargs
            if __mark_params_errors__ and param not in spec.args:
                result.append(_DoesNotExists)
                continue

            # get filtered param index
            real_positional_param_index = [arg for arg in spec.args if arg not in kwargs].index(param)
            # get function param index
            func_positional_param_index = spec.args.index(param)
            # if len of passed args gte then filtered param index add to result by index
            if len(args) > real_positional_param_index:
                result.append(args[real_positional_param_index])
            else:
                # Here we can add next check.
                #
                # if spec.defaults and len(spec.defaults) > real_positional_param_index - len(args):
                #     raise TypeError(f"{_function.__name__}() missing required argument {param}")
                #
                # But since we use signature.bind this check is not necessary. Just add to result by index
                defaults = cast("tuple[Any, ...]", spec.defaults)
                result.append(defaults[func_positional_param_index - len(spec.args) + len(defaults)])

    # add kwargs
    if need_kwargs:
        signature_parameters = signature.parameters

        _kwargs: dict[str, Any] = {}
        for key, value in kwargs.items():
            if key in signature_parameters:
                continue

            _kwargs[key] = value

        result[result.index(_Kwargs)] = _kwargs

    # add args
    if need_args:
        result[result.index(_Args)] = args[len(spec.args) :]

    return tuple(result)


def get_params_with_values(
    _function: Callable,
    _params: Sequence[str],
    *args,
    __skip_params_errors__: bool = False,
    **kwargs,
) -> dict[str, Any]:
    """Get bind values of certain parameters with params.

    Args:
        _function: Function
        _params: Params for values getting
        *args: Function arguments
        __skip_params_errors__: Skip errors if param not in signature and passed kwargs
        **kwargs: Function keyword arguments

    Returns: Dict of params with values

    """
    values = get_params_values(
        _function,
        _params,
        *args,
        __mark_params_errors__=__skip_params_errors__,
        **kwargs,
    )

    data = dict(zip(_params, values))
    if __skip_params_errors__:
        for key, value in list(data.items()):
            if value is _DoesNotExists:
                data.pop(key)

    return data
