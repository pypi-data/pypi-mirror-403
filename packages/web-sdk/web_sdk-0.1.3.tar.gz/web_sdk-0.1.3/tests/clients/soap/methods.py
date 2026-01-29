from web_sdk.core.bases import BaseService
from web_sdk.core.bases.soap import SoapMethod, SoapResponse

# noinspection PyProtectedMember
from web_sdk.types import TResponse

from . import responses as responses
from .types import Extras, Kwargs


class Service(BaseService[Kwargs, Extras]): ...


class Method(SoapMethod[TResponse, Kwargs, Extras]): ...


class FilesService(Service):
    send_file = Method[SoapResponse](path="sendFile")
    send_files = Method[SoapResponse](path="FilesService.sendFiles")
    send_two_files = Method[SoapResponse](path="sendTwoFiles")


class CommonService(Service, path="CommonService"):
    post = Method[responses.FooDataSoapResponse]()
    post_with_name = Method[responses.FooDataSoapResponse](path="postWithName")
