from web_sdk.core.bases import BaseClientService
from web_sdk.core.bases.rest.clients import BaseRestClient
from web_sdk.core.bases.rest.schemas import RestRedirectResponse
from web_sdk.core.fields import (
    APath,
)

from . import responses as responses
from .methods import MethodsService, PathsOverridesService, RedirectService
from .types import Extras, Kwargs, Settings


class _RestTestClient(BaseRestClient[Settings, Kwargs, Extras], base=True):
    __default_settings_class__ = Settings

    def __get_session__(self): ...


class RestTestClientService(BaseClientService[_RestTestClient], client=_RestTestClient): ...


class MethodsClientService(RestTestClientService):
    @MethodsService.get
    def get(self, attr: bool = True) -> responses.GetResponse: ...

    @MethodsService.post
    def post(self, attr: bool = True) -> responses.PostResponse: ...

    @MethodsService.put
    def put(self, attr: bool = True) -> responses.PutResponse: ...

    @MethodsService.patch
    def patch(self, attr: bool = True) -> responses.PatchResponse: ...

    @MethodsService.delete
    def delete(self, attr: bool = True) -> responses.DeleteResponse: ...

    @MethodsService.head
    def head(self, attr: bool = True) -> responses.HeadResponse: ...

    @MethodsService.options
    def options(self, attr: bool = True) -> responses.OptionsResponse: ...


class PathsOverridesClientService(RestTestClientService):
    @PathsOverridesService.get
    def get(self) -> responses.FooDataResponse: ...

    @PathsOverridesService.get_internal
    def get_internal(self) -> responses.FooDataResponse: ...

    @PathsOverridesService.get(paths={"scope": "all"})
    def get_all(self) -> responses.FooDataResponse: ...

    @PathsOverridesService.get
    def get_any(self, scope: APath[str]) -> responses.FooDataResponse: ...

    @PathsOverridesService.get_foo
    def get_foo(self) -> responses.FooDataResponse: ...

    @PathsOverridesService.get_foo
    def get_external_foo(self) -> responses.FooDataResponse: ...

    get_internal_foo = PathsOverridesService.get_internal_foo.from_method(get_external_foo)


class RedirectClientService(RestTestClientService):
    @RedirectService.get_redirect
    def get_redirect(self) -> RestRedirectResponse: ...


class RestTestClient(_RestTestClient):
    methods: MethodsClientService
    path_overrides: PathsOverridesClientService
    redirect: RedirectClientService
