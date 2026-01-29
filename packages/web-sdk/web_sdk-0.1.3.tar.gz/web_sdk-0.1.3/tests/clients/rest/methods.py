from web_sdk.core.bases import BaseService
from web_sdk.core.bases.rest.methods import RestMethod
from web_sdk.core.bases.rest.schemas import RestRedirectResponse
from web_sdk.enums import HTTPMethod

# noinspection PyProtectedMember
from web_sdk.types import TResponse

from . import responses as responses
from .types import Extras, Kwargs


class Service(BaseService[Kwargs, Extras]): ...


class Method(RestMethod[TResponse, Kwargs, Extras]): ...


class MethodsService(Service, path="methods"):
    get = Method[responses.GetResponse](
        method=HTTPMethod.GET,
    )
    post = Method[responses.PostResponse](
        method=HTTPMethod.POST,
    )
    put = Method[responses.PutResponse](
        method=HTTPMethod.PUT,
    )
    patch = Method[responses.PatchResponse](
        method=HTTPMethod.PATCH,
    )
    delete = Method[responses.DeleteResponse](
        method=HTTPMethod.DELETE,
    )
    head = Method[responses.HeadResponse](
        method=HTTPMethod.HEAD,
    )
    options = Method[responses.OptionsResponse](
        method=HTTPMethod.OPTIONS,
    )


class PathsOverridesService(Service, path="paths_overrides/{scope}", paths={"scope": "external"}):
    get = Method[responses.GetResponse]()
    get_internal = Method[responses.GetResponse](
        paths={"scope": "internal"},
    )
    get_foo = Method[responses.GetResponse](
        path="foo",
        paths={"scope": "external"},
    )
    get_internal_foo = Method[responses.GetResponse](
        path="foo",
        paths={"scope": "internal"},
    )


class RedirectService(Service, path=""):
    get_redirect = Method[RestRedirectResponse](
        "redirect",
    )
