from collections.abc import Callable
from typing import Annotated, Any

from typing_extensions import Unpack

from web_sdk.core.bases import BaseClient
from web_sdk.core.bases.clients import BaseClientService
from web_sdk.core.fields import ABody, ACookie, AExtra, AFile, AHeader, AKwarg, AParam, APath, ASetting, Param
from web_sdk.utils.contextvar import SimpleContext

from .methods import ExtrasService, Method, OthersService
from .responses import (
    BaseTestRequestErrorResponse,
    BaseTestResponse,
    BaseTestResponseErrorResponse,
    BaseTestRetryErrorResponse,
)
from .types import Context, Extras, Kwargs, KwargsForTestUnpack, ModelForTest, Settings

_context = SimpleContext[Context](
    default_factory=lambda: Context(
        method=None,
        kwargs={},
        extras={},
    )
)


class _BaseTestClient(BaseClient[Method, Context, Settings, Kwargs, Extras], base=True, __context__=_context):
    __default_settings_class__ = Settings
    __request_error_response__ = BaseTestRequestErrorResponse
    __response_error_response__ = BaseTestResponseErrorResponse
    __retry_error_response__ = BaseTestRetryErrorResponse

    def __get_session__(self): ...
    def _get_request_method(self) -> Callable[..., Any]:
        return self._session.method

    def _call_request_method(self, request_method: Callable[..., Any]) -> Any:
        return self._get_request_method()(**self.kwargs)


class BaseTestClientService(BaseClientService, client=_BaseTestClient): ...


class ExtrasClientService(BaseTestClientService):
    @ExtrasService.get(extras=Extras(extra3=True))
    def get(self, extra4: AExtra[bool] = True) -> BaseTestResponse: ...


class SignatureClientService(BaseTestClientService):
    @OthersService.signature
    def signature_no_annotated(self, attr: int) -> BaseTestResponse: ...

    @OthersService.signature
    def signature_annotated_not_call(self, attr: Annotated[int, Param]) -> BaseTestResponse: ...

    @OthersService.signature
    def signature_annotated_not_call_with_default(self, attr: Annotated[int, Param] = 0) -> BaseTestResponse: ...

    @OthersService.signature
    def signature_annotated_call(self, attr: Annotated[int, Param(lt=2)]) -> BaseTestResponse: ...

    @OthersService.signature
    def signature_annotated_call_with_default(self, attr: Annotated[int, Param(lt=2)] = 0) -> BaseTestResponse: ...

    @OthersService.signature
    def signature_as_default_not_call(self, attr: int = Param) -> BaseTestResponse: ...  # type: ignore

    @OthersService.signature
    def signature_as_default_call(self, attr: int = Param(lt=2)) -> BaseTestResponse: ...  # type: ignore

    @OthersService.signature
    def signature_as_default_call_with_default(
        self,
        attr: int = Param(default=0, lt=2),  # type: ignore
    ) -> BaseTestResponse: ...

    @OthersService.signature
    def signature_annotated_as_a(self, attr: AParam[int]) -> BaseTestResponse: ...

    @OthersService.signature
    def signature_annotated_as_a_with_default(self, attr: AParam[int] = 0) -> BaseTestResponse: ...

    @OthersService.signature
    def full(
        self,
        param1: bool = True,
        param2: AParam[bool] = True,
        body1: ABody[bool] = True,
        body2: ABody[bool] = True,
        header1: AHeader[bool] = True,
        header2: AHeader[bool] = True,
        file1: AFile[bytes] = b"1",
        file2: AFile[bytes] = b"1",
        cookie1: ACookie[bool] = True,
        cookie2: ACookie[bool] = True,
        path1: APath[str] = "path1",
        path2: APath[str] = "path2",
        kwarg1: AKwarg[bool] = True,
        kwarg2: AKwarg[bool] = True,
        extra1: AExtra[bool] = True,
        extra2: AExtra[bool] = True,
        test_mode: ASetting[bool | None] = None,
        raise_exceptions: ASetting[bool | None] = None,
    ) -> BaseTestResponse: ...

    @OthersService.signature
    def unpacked_kwargs(
        self,
        required_function_param: bool,
        required_pydantic_function_body: ABody[ModelForTest],  # type: ignore
        not_required_function_body: ABody[bool] = True,
        **kwargs: Unpack[KwargsForTestUnpack],
    ) -> BaseTestResponse: ...


class SettingsClientService(BaseTestClientService):
    @OthersService.check_settings
    def check_settings(
        self,
        raise_exceptions: ASetting[bool | None] = None,
        test_mode: ASetting[bool | None] = None,
        skip_for_test: ASetting[bool | None] = None,
        fake_for_test: ASetting[bool | None] = None,
        max_retry_count: ASetting[bool | None] = None,
        max_retry_count_after_disconnect: ASetting[bool | None] = None,
    ) -> BaseTestResponse: ...


class ValidatedClientService(BaseTestClientService):
    @OthersService.get_success_validated_data
    def get_success_validated_data(self) -> BaseTestResponse: ...

    @OthersService.get_failure_validated_data
    def get_failure_validated_data(self) -> BaseTestResponse: ...


class BaseTestClient(_BaseTestClient):
    extras_: ExtrasClientService
    signature: SignatureClientService
    settings: SettingsClientService
    validated: ValidatedClientService
