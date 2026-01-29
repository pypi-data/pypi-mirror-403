"""Soap context value type."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from web_sdk.core.bases.soap.methods import SoapMethod
from web_sdk.core.context import ContextData
from web_sdk.types import TExtras, TKwargs

if TYPE_CHECKING:
    from typing_extensions import Required

    from web_sdk.core.bases.soap.files import SoapFile


# noinspection PyTypedDict
class SoapContextData(ContextData[SoapMethod, TKwargs, TExtras], Generic[TKwargs, TExtras]):
    """Rest request context data."""

    files: Required[list[SoapFile]]
    boundary: Required[str]
    content_id: Required[str]
