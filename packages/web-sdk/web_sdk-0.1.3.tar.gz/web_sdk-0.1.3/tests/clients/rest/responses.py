from typing import Any, Generic

from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.core.bases.rest import BaseRestDataResponse
from web_sdk.types import TData


class _FooData(PydanticModel):
    class _NestedData(PydanticModel):
        nested_attr: int

    attr: int
    nested_attr: _NestedData


class GetData(PydanticModel): ...


class PostData(PydanticModel): ...


class PutData(PydanticModel): ...


class PatchData(PydanticModel): ...


class DeleteData(PydanticModel): ...


class HeadData(PydanticModel): ...


class OptionsData(PydanticModel): ...


class DataResponse(BaseRestDataResponse[TData], Generic[TData]):
    @classmethod
    def _extract_data(cls, response: Any) -> Any:
        return response


GetResponse = DataResponse[GetData]
PostResponse = DataResponse[PostData]
PutResponse = DataResponse[PutData]
PatchResponse = DataResponse[PatchData]
DeleteResponse = DataResponse[DeleteData]
HeadResponse = DataResponse[HeadData]
OptionsResponse = DataResponse[OptionsData]

FooDataResponse = DataResponse[_FooData]
