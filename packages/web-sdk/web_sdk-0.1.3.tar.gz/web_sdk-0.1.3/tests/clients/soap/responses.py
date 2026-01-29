from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.core.bases.soap import SoapResponse


class FooDataSoapResponse(SoapResponse):
    class _NestedData(PydanticModel):
        nested_attr: int

    attr: int
    nested_attr: _NestedData
