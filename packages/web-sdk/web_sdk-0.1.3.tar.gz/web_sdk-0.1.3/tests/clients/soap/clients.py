from web_sdk.core.bases import BaseClientService
from web_sdk.core.bases.soap import BaseSoapClient, SoapFile, SoapResponse
from web_sdk.core.fields import (
    AFile,
)

from . import responses as responses
from .methods import CommonService, FilesService
from .types import Extras, FooData, Kwargs, Settings


class _SoapTestClient(BaseSoapClient[Settings, Kwargs, Extras], base=True):
    __default_settings_class__ = Settings

    def __get_session__(self): ...


class SoapTestClientService(BaseClientService[_SoapTestClient], client=_SoapTestClient): ...


class FilesClientService(SoapTestClientService):
    @FilesService.send_file
    def send_file(self, file: AFile[SoapFile], attr: bool = False) -> SoapResponse: ...

    @FilesService.send_files
    def send_files(self, files: AFile[list[SoapFile]], attr: bool = False) -> SoapResponse: ...

    @FilesService.send_two_files
    def send_two_files(self, file1: AFile[SoapFile], file2: AFile[SoapFile]) -> SoapResponse: ...


class CommonClientService(SoapTestClientService):
    @CommonService.post
    def post(self, attr: bool, nested: FooData) -> responses.FooDataSoapResponse: ...

    @CommonService.post_with_name
    def post_with_name(self, attr: bool, nested: FooData) -> responses.FooDataSoapResponse: ...


class SoapTestClient(_SoapTestClient):
    files: FilesClientService
    common: CommonClientService
