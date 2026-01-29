"""Custom transport classes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from zeep import Transport
from zeep.wsdl.utils import etree_to_string

from web_sdk.types import TExtras, TKwargs

if TYPE_CHECKING:
    from collections.abc import Iterable

    from zeep.cache import Base as BaseCache

    from web_sdk.core.bases.soap.context import SoapContextData
    from web_sdk.core.bases.soap.files import SoapFile
    from web_sdk.utils.contextvar import SimpleContext


class FileTransport(Transport, Generic[TKwargs, TExtras]):
    """Custom transport class for files sending support."""

    _NEW_LINE = b"\r\n"
    """New line part"""

    _context: SimpleContext[SoapContextData[TKwargs, TExtras]]

    def __init__(
        self,
        context: SimpleContext[SoapContextData[TKwargs, TExtras]],
        cache: BaseCache | None = None,
        timeout: int = 300,
        operation_timeout: int | None = None,
        session=None,
    ):
        """Init transport instance.

        Args:
            context: soap request context
            cache: The cache object to be used to cache GET requests
            timeout: The timeout for loading wsdl and xsd documents
            operation_timeout: The timeout for operations (POST/GET). By default, this is None (no timeout).
            session: request.Session

        """
        self._context = context
        super().__init__(cache=cache, timeout=timeout, operation_timeout=operation_timeout, session=session)

    @property
    def context(self) -> SoapContextData[TKwargs, TExtras]:
        """Return SimpleContext instance value."""
        return self._context.value  # type: ignore

    @staticmethod
    def _format_bytes(target: bytes, values: Iterable[str]) -> bytes:
        """Format bytes string."""
        return (target % values).replace(b"'", b"")

    def _get_main_part(self, envelope) -> bytes:
        """Return XML part of soap request."""
        header = self._NEW_LINE.join(
            [
                self._format_bytes(b"--%a", (self.context["boundary"],)),
                b"Content-Type: text/xml; charset=UTF-8",
                b"Content-Transfer-Encoding: 8bit",
                self._format_bytes(b"Content-ID: %a", (self.context["content_id"],)),
            ]
        )
        data = etree_to_string(envelope)

        return self._NEW_LINE.join([header, b"", data])

    def _get_attachment_part(self, soap_file: SoapFile) -> bytes:
        """Return file part of soap request."""
        header = self._NEW_LINE.join(
            [
                self._format_bytes(b"--%a", (self.context["boundary"],)),
                self._format_bytes(b"Content-Transfer-Encoding: %a", (soap_file.transfer_encoding,)),
                self._format_bytes(b'Content-Type: %a; name="%a"', (soap_file.content_type, soap_file.filename)),
                self._format_bytes(b"Content-ID: <%a>", (soap_file.content_id,)),
                self._format_bytes(
                    b'Content-Disposition: attachment; name="%a"; filename="%a"',
                    (soap_file.filename, soap_file.filename),
                ),
            ]
        )

        return self._NEW_LINE.join([header, b"", soap_file.data])

    def _get_multipart_related_message(self, envelope) -> bytes:
        """Get joined multipart related message."""
        return self._NEW_LINE.join(
            [
                # XML part
                self._get_main_part(envelope),
                # attachments parts
                *(
                    attachment_part
                    for file in self.context["files"]
                    if (attachment_part := self._get_attachment_part(file))
                ),
                # closing boundary
                self._format_bytes(b"--%a--", (self.context["boundary"],)),
            ]
        )

    def _set_multipart_related_headers(self, headers: dict, message: bytes):
        """Set content headers for multipart related messages."""
        headers["Content-Type"] = "; ".join(
            [
                "multipart/related",
                f'boundary="{self.context["boundary"]}"',
                'type="text/xml"',
                f'start="{self.context["content_id"]}"',
                "charset=utf-8",
            ]
        )
        headers["Content-Length"] = str(len(message))

    def post_xml(self, address, envelope, headers):
        """Post XML message (optional with attachments)."""
        # if no files call super method
        if not self.context["files"]:
            return super().post_xml(address, envelope, headers)

        # otherwise make message with attachments parts
        message = self._get_multipart_related_message(envelope)
        # set multipart/related headers
        self._set_multipart_related_headers(headers, message)
        # post message
        return self.post(address, message, headers)
