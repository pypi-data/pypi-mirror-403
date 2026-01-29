from unittest.mock import MagicMock

import pytest

from tests.clients.soap.clients import SoapTestClient
from tests.clients.soap.methods import CommonService, FilesService
from tests.clients.soap.types import FooData, FooNestedData
from web_sdk.core.bases.soap import SoapFile
from web_sdk.utils.cgi import parse_header

NL = "\r\n"


@pytest.fixture(autouse=True)
def mock_client_get_session(mocker):
    mocker.patch("zeep.wsdl.bindings.soap.SoapBinding.process_reply")
    mocker.patch.object(SoapTestClient, "__get_session__", return_value=MagicMock())


@pytest.fixture
def client() -> SoapTestClient:
    return SoapTestClient()


def test_soap_method_path(client):
    assert FilesService.send_file.path == "sendFile"
    assert FilesService.send_files.path == "FilesService.sendFiles"
    assert CommonService.post.path == "CommonService.post"
    assert CommonService.post_with_name.path == "CommonService.postWithName"


def test_send_file(client):
    file = SoapFile(
        filename="example.txt",
        content=b"content",
        content_type="text/plain",
    )
    file_content_id = file.content_id
    file_base64 = file.base64

    client.files.send_file(attr=True, file=file)
    _, kwargs = client._session.post.call_args
    _, content_params = parse_header(kwargs["headers"]["Content-Type"])
    boundary = content_params["boundary"]
    main_content_id = content_params["start"]

    assert (
        kwargs["data"]
        == (
            f"--{boundary}{NL}"
            f"Content-Type: text/xml; charset=UTF-8{NL}"
            f"Content-Transfer-Encoding: 8bit{NL}"
            f"Content-ID: {main_content_id}{NL}{NL}"
            f"<?xml version='1.0' encoding='utf-8'?>\n"
            f'<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">'
            f"<soap-env:Body>"
            f'<ns0:SendFileRequest xmlns:ns0="urn:ws">'
            f"<ns0:attr>true</ns0:attr>"
            f"</ns0:SendFileRequest></soap-env:Body>"
            f"</soap-env:Envelope>{NL}"
            f"--{boundary}{NL}"
            f"Content-Transfer-Encoding: base64{NL}"
            f"Content-Type: text/plain; "
            f'name="{file.filename}"{NL}'
            f"Content-ID: <{file_content_id}>{NL}"
            f"Content-Disposition: attachment; "
            f'name="{file.filename}"; '
            f'filename="{file.filename}"{NL}{NL}'
            f"{file_base64.decode()}{NL}"
            f"--{boundary}--"
        ).encode()
    )


def test_send_files(client):
    file1 = SoapFile(
        filename="example1.txt",
        content=b"content1",
        content_type="text/plain",
    )
    file1_content_id = file1.content_id
    file1_base64 = file1.base64

    file2 = SoapFile(filename="example2.txt", content=b"content2", content_type="text/plain", to_base_64=False)
    file2_content_id = file2.content_id

    client.files.send_files(attr=True, files=[file1, file2])

    _, kwargs = client._session.post.call_args
    _, content_params = parse_header(kwargs["headers"]["Content-Type"])

    boundary = content_params["boundary"]
    main_content_id = content_params["start"]

    assert (
        kwargs["data"]
        == (
            f"--{boundary}{NL}"
            f"Content-Type: text/xml; charset=UTF-8{NL}"
            f"Content-Transfer-Encoding: 8bit{NL}"
            f"Content-ID: {main_content_id}{NL}{NL}"
            f"<?xml version='1.0' encoding='utf-8'?>\n"
            f'<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">'
            f"<soap-env:Body>"
            f'<ns0:FilesService.SendFilesRequest xmlns:ns0="urn:ws">'
            f"<ns0:attr>true</ns0:attr>"
            f"</ns0:FilesService.SendFilesRequest></soap-env:Body>"
            f"</soap-env:Envelope>{NL}"
            f"--{boundary}{NL}"
            f"Content-Transfer-Encoding: {file1.transfer_encoding}{NL}"
            f"Content-Type: text/plain; "
            f'name="{file1.filename}"{NL}'
            f"Content-ID: <{file1_content_id}>{NL}"
            f"Content-Disposition: attachment; "
            f'name="{file1.filename}"; '
            f'filename="{file1.filename}"{NL}{NL}'
            f"{file1_base64.decode()}{NL}"
            f"--{boundary}{NL}"
            f"Content-Transfer-Encoding: {file2.transfer_encoding}{NL}"
            f"Content-Type: text/plain; "
            f'name="{file2.filename}"{NL}'
            f"Content-ID: <{file2_content_id}>{NL}"
            f"Content-Disposition: attachment; "
            f'name="{file2.filename}"; '
            f'filename="{file2.filename}"{NL}{NL}'
            f"{file2.content.decode()}{NL}"
            f"--{boundary}--"
        ).encode()
    )


def test_files_in_different_attrs(client):
    file1 = SoapFile(
        filename="example1.txt",
        content=b"content1",
        content_type="text/plain",
    )
    file1_content_id = file1.content_id
    file1_base64 = file1.base64

    file2 = SoapFile(
        filename="example2.txt",
        content=b"content2",
        content_type="text/plain",
        to_base_64=False,
    )
    file2_content_id = file2.content_id

    client.files.send_two_files(file1=file1, file2=file2)

    _, kwargs = client._session.post.call_args
    _, content_params = parse_header(kwargs["headers"]["Content-Type"])

    boundary = content_params["boundary"]
    main_content_id = content_params["start"]

    assert (
        kwargs["data"]
        == (
            f"--{boundary}{NL}"
            f"Content-Type: text/xml; charset=UTF-8{NL}"
            f"Content-Transfer-Encoding: 8bit{NL}"
            f"Content-ID: {main_content_id}{NL}{NL}"
            f"<?xml version='1.0' encoding='utf-8'?>\n"
            f'<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">'
            f"<soap-env:Body>"
            f'<ns0:SendTwoFilesRequest xmlns:ns0="urn:ws"/>'
            f"</soap-env:Body>"
            f"</soap-env:Envelope>{NL}"
            f"--{boundary}{NL}"
            f"Content-Transfer-Encoding: {file1.transfer_encoding}{NL}"
            f"Content-Type: text/plain; "
            f'name="{file1.filename}"{NL}'
            f"Content-ID: <{file1_content_id}>{NL}"
            f"Content-Disposition: attachment; "
            f'name="{file1.filename}"; '
            f'filename="{file1.filename}"{NL}{NL}'
            f"{file1_base64.decode()}{NL}"
            f"--{boundary}{NL}"
            f"Content-Transfer-Encoding: {file2.transfer_encoding}{NL}"
            f"Content-Type: text/plain; "
            f'name="{file2.filename}"{NL}'
            f"Content-ID: <{file2_content_id}>{NL}"
            f"Content-Disposition: attachment; "
            f'name="{file2.filename}"; '
            f'filename="{file2.filename}"{NL}{NL}'
            f"{file2.content.decode()}{NL}"
            f"--{boundary}--"
        ).encode()
    )


def test_common(client):
    client.common.post(attr=True, nested=FooData(attr=True, nested=FooNestedData(attr=True)))
    _, kwargs = client._session.post.call_args

    assert kwargs["data"] == (
        b"<?xml version='1.0' encoding='utf-8'?>\n"
        b'<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">'
        b'<soap-env:Body><ns0:CommonClientService.postRequest xmlns:ns0="urn:ws">'
        b"<ns0:attr>true</ns0:attr>"
        b"<ns0:nested>"
        b"<ns0:attr>true</ns0:attr>"
        b"<ns0:nested>"
        b"<ns0:attr>true</ns0:attr>"
        b"</ns0:nested>"
        b"</ns0:nested>"
        b"</ns0:CommonClientService.postRequest></soap-env:Body></soap-en"
        b"v:Envelope>"
    )

    client.common.post_with_name(attr=True, nested=FooData(attr=True, nested=FooNestedData(attr=True)))
    _, kwargs = client._session.post.call_args

    assert kwargs["data"] == (
        b"<?xml version='1.0' encoding='utf-8'?>\n"
        b'<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/">'
        b'<soap-env:Body><ns0:CommonClientService.postWithNameRequest xmlns:ns0="urn:ws">'
        b"<ns0:attr>true</ns0:attr>"
        b"<ns0:nested>"
        b"<ns0:attr>true</ns0:attr>"
        b"<ns0:nested>"
        b"<ns0:attr>true</ns0:attr>"
        b"</ns0:nested>"
        b"</ns0:nested>"
        b"</ns0:CommonClientService.postWithNameRequest></soap-env:Body></soap-en"
        b"v:Envelope>"
    )


def test_client_get_transport_without_context(client, mocker):
    mocker.patch.object(client, "__context__", new=None)

    with pytest.raises(AttributeError, match="Attribute __context__ must be set."):
        client.__get_transport__(None)
