from typing_extensions import TypedDict

from web_sdk.core.bases import BaseSDKSettings
from web_sdk.core.bases.rest.kwargs import RestFieldsKwargs


class Kwargs(RestFieldsKwargs, total=False): ...


class Extras(TypedDict, total=False): ...


class Settings(BaseSDKSettings): ...
