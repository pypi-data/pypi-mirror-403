"""Rest context value type."""

from typing import Generic

from web_sdk.core.bases.rest.methods import RestMethod
from web_sdk.core.context import ContextData
from web_sdk.types import TExtras, TKwargs


# noinspection PyTypedDict
class RestContextData(ContextData[RestMethod, TKwargs, TExtras], Generic[TKwargs, TExtras]):
    """Rest request context data."""
