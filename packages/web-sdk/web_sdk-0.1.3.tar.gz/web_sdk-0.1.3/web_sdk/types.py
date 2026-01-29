"""Module types."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, TypeAlias

from typing_extensions import ParamSpec, TypedDict, TypeVar

if TYPE_CHECKING:
    from web_sdk.core.bases import BaseSDKSettings
    from web_sdk.core.context import ContextData
    from web_sdk.core.interfaces import IMethod
    from web_sdk.enums import LogLevel

T = TypeVar("T")
S = TypeVar("S")
P = ParamSpec("P")
R = TypeVar("R", covariant=True)


class __TypedDict(TypedDict): ...


ATypedDict: TypeAlias = __TypedDict
TTypedDict = TypeVar("TTypedDict", bound=ATypedDict)


class PLogger(Protocol):
    """Logger protocol for support logging as logger annotation."""

    name: str

    def log(self, level: LogLevel, msg: str, *args, **kwargs):
        """Record log message."""


TResponse = TypeVar("TResponse")
"""Request response type var"""


TKwargs = TypeVar("TKwargs", bound=ATypedDict)
"""Request kwargs type var"""
TExtras = TypeVar("TExtras", ATypedDict, dict, default=dict)
"""Request extras type var"""
TData = TypeVar("TData")
"""Request response data type var"""

TClient = TypeVar("TClient")
"""Client type var"""

if TYPE_CHECKING:
    TMethod = TypeVar("TMethod", bound=IMethod)
    """SDK Method type var"""
    TSettings = TypeVar("TSettings", bound=BaseSDKSettings)
    """Client settings type var"""
    # noinspection PyTypeHints
    TContext = TypeVar("TContext", bound=ContextData)  # pyright: ignore [reportGeneralTypeIssues]
    """Request context type var"""
else:
    TMethod = TypeVar("TMethod")
    TSettings = TypeVar("TSettings")
    TContext = TypeVar("TContext")

PartsNames: TypeAlias = (
    Literal["paths", "body", "headers", "params", "files", "cookies", "kwargs", "extras", "settings"] | str
)


class PMethod(Protocol[P, TResponse]):
    """Protocol for method."""

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> TResponse: ...  # noqa
