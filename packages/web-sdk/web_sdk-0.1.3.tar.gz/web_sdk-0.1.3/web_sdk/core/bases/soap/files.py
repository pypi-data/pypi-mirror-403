"""Module with utils for working with SOAP files."""

import base64
import hashlib
from functools import cached_property
from typing import Any, Literal

from pydantic import ModelWrapValidatorHandler, PrivateAttr, model_validator
from typing_extensions import Self
from zeep.wsdl.attachments import Attachment

from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.utils.cgi import parse_header
from web_sdk.utils.uuid import get_uuid_chars


class SoapFile(PydanticModel):
    """Container for working with soap file."""

    filename: str
    """File name"""
    content: bytes
    """File content"""
    content_type: str
    """Content type of the file"""
    size: int | None = None
    """File size"""
    extension: str | None = None
    """File extension"""
    to_base_64: bool = True
    """Convert file content to base64 for sending"""

    _content_id: str | None = PrivateAttr(None)

    @property
    def transfer_encoding(self) -> Literal["base64", "binary"]:
        """Content transfer encoding."""
        return "base64" if self.to_base_64 else "binary"

    @cached_property
    def base64(self) -> bytes:
        """Base64 encoded content."""
        return base64.b64encode(self.content)

    @cached_property
    def md5(self) -> str:
        """Return md5 hash of file content."""
        return hashlib.md5(self.content).hexdigest()

    @property
    def data(self) -> bytes:
        """Data for sending."""
        return self.base64 if self.to_base_64 else self.content

    @property
    def content_id(self) -> str:
        """Content ID of soap file."""
        # not cached_property for support getting content_id from other object
        if self._content_id is not None:
            return self._content_id

        self._content_id = get_uuid_chars()
        return self._content_id

    @model_validator(mode="wrap")
    @classmethod
    def _set_content_type(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        """Save original object."""
        validated_self = handler(data)
        if isinstance(data, Attachment):
            validated_self._content_id = data.content_id[1:-1]
        return validated_self

    @model_validator(mode="before")
    @classmethod
    def _validate(cls, attachment: Any):
        """Validate the file from soap attachment."""
        # if we get file not from soap response return
        if not isinstance(attachment, Attachment):
            return attachment

        # get content type from attachment
        content_type = attachment.content_type.split(";")[0]
        # parse params from content disposition header
        _, params = parse_header(attachment.headers.get("Content-Disposition", ""))
        # try to get filename
        filename = params.get("filename", "No name")
        # try to get extension from file name
        extension = filename.split(".")[-1] if "." in filename else None
        # get content from attachment
        content = attachment.content
        # try to get file size from content disposition or content
        size = params["size"] if "size" in params else len(content)
        # return valid dict
        return dict(
            filename=filename,
            content=content,
            content_type=content_type,
            size=size,
            extension=extension,
        )
