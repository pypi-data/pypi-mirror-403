import json

import pytest
import xmltodict
from requests import Response

from web_sdk.consts import HTTP_200_OK
from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.core.backends.requests.rest.schemas import import_xmltodict
from web_sdk.sdks.rest import JsonResponse, XmlResponse


class _FooData(PydanticModel):
    class _Response(PydanticModel):
        class _Data(PydanticModel):
            attr1: int
            attr2: str

        status: str

    response: _Response


_test_data = {
    "response": {
        "status": "status",
        "data": {
            "attr1": 1,
            "attr2": "string",
        },
    }
}
_json_test_data = json.dumps(_test_data).encode()
_xml_test_data = xmltodict.unparse(_test_data).encode()


@pytest.mark.parametrize(
    "data,raw_data,response_type",
    [
        (_test_data, _json_test_data, JsonResponse[_FooData]),
        (_test_data, _xml_test_data, XmlResponse[_FooData]),
    ],
    ids=["json", "xml"],
)
def test_response(data, raw_data, response_type):
    raw_response = Response()
    raw_response._content = raw_data
    raw_response.status_code = HTTP_200_OK

    response = response_type.model_validate(raw_response, from_attributes=True)
    assert response.content == raw_data
    assert response.text == raw_data.decode()
    assert response.result == _FooData.model_validate(data)


def test_xmltodict_installed(mocker):
    mocker.patch("web_sdk.core.backends.requests.rest.schemas.xmltodict", xmltodict)

    class FooXmlResponse(XmlResponse): ...

    rwa_response = Response()
    rwa_response._content = b'<?xml version="1.0" encoding="utf-8"?><attr></attr>'
    rwa_response.status_code = HTTP_200_OK

    FooXmlResponse.model_validate(rwa_response, from_attributes=True)


def test_xmltodict_not_installed(mocker):
    mocker.patch("web_sdk.core.backends.requests.rest.schemas.xmltodict", None)
    mocker.patch("web_sdk.core.backends.requests.rest.schemas.import_xmltodict", side_effect=ImportError)

    class FooXmlResponse(XmlResponse[_FooData]): ...

    with pytest.raises(ImportError):
        FooXmlResponse.model_validate(Response(), from_attributes=True)


def test_import_xmltodict_not_installed(mocker):
    mocker.patch.dict("sys.modules", {"xmltodict": None})
    with pytest.raises(ImportError, match=r"xmltodict is not installed, run `pip install 'web-sdk\[xml\]'`"):
        import_xmltodict()
