import os

from pydantic import computed_field
from typing_extensions import TypedDict

from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.core.bases.rest.kwargs import RestFieldsKwargs
from web_sdk.core.bases.soap.settings import BaseSoapSettings

this_files_dir = os.path.dirname(os.path.realpath(__file__))
wsdl_path = os.path.join(this_files_dir, "test.wsdl")


class Kwargs(RestFieldsKwargs, total=False): ...


class Extras(TypedDict, total=False): ...


class Settings(BaseSoapSettings):
    service_name: str | None = "ws"
    port_name: str | None = "wsPort"

    @computed_field
    @property
    def url(self) -> str:
        return wsdl_path


class FooNestedData(PydanticModel):
    attr: bool


class FooData(PydanticModel):
    attr: bool
    nested: FooNestedData
