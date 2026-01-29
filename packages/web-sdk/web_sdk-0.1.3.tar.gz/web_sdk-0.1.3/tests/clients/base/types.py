from typing import Annotated

from typing_extensions import NotRequired, Required, TypedDict

from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.core.bases import BaseSDKSettings
from web_sdk.core.bases.rest.kwargs import RestFieldsKwargs
from web_sdk.core.context import ContextData
from web_sdk.core.fields import ABody, AExtra, AKwarg, AParam, Body
from web_sdk.core.kwargs import RequestSettingsKwargs


class Kwargs(RestFieldsKwargs, total=False):
    kwarg1: AKwarg[bool | None]
    kwarg2: AKwarg[bool | None]


class Extras(TypedDict, total=False):
    extra1: AExtra[bool | None]
    extra2: AExtra[bool | None]
    extra3: AExtra[bool | None]
    extra4: AExtra[bool | None]


class ModelForTest(PydanticModel):
    attr1: bool
    attr2: bool


class KwargsForTestUnpack(Kwargs, RequestSettingsKwargs, Extras):
    required_param: Required[AParam[bool]]
    not_required_param: NotRequired[AParam[bool | None]]
    not_required_body_with_default: NotRequired[Annotated[bool | None, Body(True)]]
    required_param_without_annotation: Annotated[bool, object]
    not_required_param_without_annotation: NotRequired[bool | None]
    required_pydantic_body: ABody[ModelForTest]
    required_pydantic_extra: AExtra[ModelForTest]


class Settings(BaseSDKSettings): ...


class Context(ContextData): ...
