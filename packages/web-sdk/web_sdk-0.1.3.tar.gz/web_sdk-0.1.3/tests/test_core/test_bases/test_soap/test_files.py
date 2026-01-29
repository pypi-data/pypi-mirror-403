import base64

from zeep.wsdl.attachments import Attachment as ZeepAttachment

from web_sdk.contrib.pydantic.utils import convert
from web_sdk.core.bases.soap import SoapFile


def test_send_file():
    content = b"content"

    file_binary = SoapFile(
        filename="example.txt",
        content=content,
        to_base_64=False,
        content_type="text/plain",
    )
    file_base64 = SoapFile(
        filename="example.txt",
        content=content,
        content_type="text/plain",
    )

    assert file_binary.data == content
    assert file_binary.transfer_encoding == "binary"

    assert file_base64.data == file_base64.base64
    assert file_base64.transfer_encoding == "base64"

    assert file_base64.md5 == file_binary.md5
    assert file_base64.content_id != file_binary.content_id
    assert file_base64.content_id == file_base64.content_id


def test_parse_file():
    file_name = "example.txt"
    content_id = "content_id"
    content = b"content"
    base64_content = base64.b64encode(content)

    class Part:
        headers = {
            b"Content-Transfer-Encoding": b"base64",
            b"Content-Type": f'text/plain;name="{file_name}"'.encode(),
            b"Content-ID": f"<{content_id}>".encode(),
            b"Content-Disposition": f'attachment; name="{file_name}"; filename="{file_name}"'.encode(),
        }
        encoding = "utf-8"
        content = base64_content

    file = convert(SoapFile, ZeepAttachment(Part), from_attributes=True)
    assert file.content == content
    assert file.content_id == content_id
    assert file.filename == file_name
    assert file.size == len(content)
    assert file.content_type == "text/plain"
