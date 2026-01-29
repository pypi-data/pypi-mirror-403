"""Utils for type annotations."""

from __future__ import annotations

import inspect
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal, ParamSpec, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Callable

P1 = ParamSpec("P1")
R1 = TypeVar("R1", covariant=True)
P2 = ParamSpec("P2")
R2 = TypeVar("R2", covariant=True)


@overload
def signature_from(  # pyright: ignore [reportOverlappingOverload]
    donor: Callable[P1, R1], __params__: Literal[True] = True, __return__: Literal[True] = True
) -> Callable[[Callable[..., Any]], Callable[P1, R1]]: ...
@overload
def signature_from(
    donor: Callable[P1, R1], __params__: Literal[False] = False, __return__: Literal[True] = True
) -> Callable[[Callable[P2, Any]], Callable[P2, R1]]: ...
@overload
def signature_from(
    donor: Callable[P1, R1], __params__: Literal[True] = True, __return__: Literal[False] = False
) -> Callable[[Callable[..., R2]], Callable[P1, R2]]: ...
@overload
def signature_from(  # pyright: ignore [reportOverlappingOverload]
    donor: Callable[P1, R1], __params__: Literal[False] = False, __return__: Literal[False] = False
) -> Callable[[Callable[P2, R2]], Callable[P2, R2]]: ...
def signature_from(
    donor: Callable[P1, R1], __params__: bool = True, __return__: bool = True
) -> Callable[
    [Callable[P2, R2]],
    Callable[P1, R1] | Callable[P2, R1] | Callable[P1, R2] | Callable[P2, R2],
]:
    """Copy signature from function."""
    donor_signature = inspect.signature(donor)

    def decorator(
        recipient: Callable[P2, R2],
    ) -> Callable[P1, R1] | Callable[P2, R1] | Callable[P1, R2] | Callable[P2, R2]:
        recipient_signature = inspect.signature(recipient)

        parameters = donor_signature.parameters if __params__ else recipient_signature.parameters
        return_annotation = donor_signature.return_annotation if __return__ else recipient_signature.return_annotation

        signature = inspect.Signature(list(parameters.values()), return_annotation=return_annotation)
        recipient.__signature__ = signature  # pyright: ignore [reportFunctionMemberAccess]

        @wraps(recipient)
        def wrapper(*args, **kwargs):
            return recipient(*args, **kwargs)

        return wrapper

    return decorator
