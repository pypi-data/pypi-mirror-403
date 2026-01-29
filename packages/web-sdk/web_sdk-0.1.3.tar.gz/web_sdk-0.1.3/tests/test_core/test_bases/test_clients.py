import logging
from abc import ABC
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from tests.clients.base.clients import BaseTestClient, BaseTestClientService
from tests.clients.base.methods import OthersService
from tests.clients.base.responses import (
    BaseTestRequestErrorResponse,
    BaseTestResponse,
    BaseTestResponseErrorResponse,
    BaseTestRetryErrorResponse,
)
from tests.clients.base.types import ModelForTest, Settings
from web_sdk.contrib.pydantic.models import ProxyModel
from web_sdk.core.bases import BaseClient
from web_sdk.core.exceptions import (
    FailureRequestSDKException,
    MaxRetriesAfterDisconnectSDKException,
    MaxRetriesSDKException,
    UnexpectedSDKException,
)
from web_sdk.enums import LogLevel, TokenType
from web_sdk.utils.contextvar import SimpleContext
from web_sdk.utils.exceptions import ExceptionModel


@pytest.fixture(autouse=True)
def mock_client_get_session(mocker):
    mocker.patch.object(BaseTestClient, "__get_session__", return_value=MagicMock())


@pytest.fixture
def client() -> BaseTestClient:
    return BaseTestClient()


def test_extras(client, mocker):
    make_request = mocker.patch.object(BaseTestClient, "make_request")
    client.extras_.get(extra4=True)

    # noinspection PyUnresolvedReferences
    _, kwargs = make_request.call_args  # pyright: ignore [reportAttributeAccessIssue]
    assert kwargs["extras"] == {
        "extra1": True,
        "extra2": True,
        "extra3": True,
        "extra4": True,
    }


@pytest.mark.parametrize(
    "function,is_default",
    [
        ("signature_no_annotated", False),
        ("signature_annotated_not_call", False),
        ("signature_annotated_not_call_with_default", True),
        ("signature_annotated_not_call_with_default", False),
        ("signature_annotated_call", False),
        ("signature_annotated_call_with_default", True),
        ("signature_annotated_call_with_default", False),
        ("signature_as_default_not_call", False),
        ("signature_as_default_call", False),
        ("signature_as_default_call_with_default", True),
        ("signature_as_default_call_with_default", False),
        ("signature_annotated_as_a", False),
        ("signature_annotated_as_a_with_default", True),
        ("signature_annotated_as_a_with_default", False),
    ],
)
def test_signature_success_calls(client, function, is_default):
    attr_value = 0 if is_default else 1
    attrs = {} if is_default else {"attr": attr_value}
    getattr(client.signature, function)(**attrs)

    _, kwargs = client._session.method.call_args
    assert kwargs["params"]["attr"] == attr_value


@pytest.mark.parametrize(
    "function",
    [
        "signature_annotated_call",
        "signature_annotated_call_with_default",
        "signature_as_default_call",
        "signature_as_default_call_with_default",
    ],
)
def test_signature_failure_calls(client, function):
    with pytest.raises(ValidationError, match="Input should be less than 2 .*"):
        getattr(client.signature, function)(attr=2)


def test_signature_full(client, mocker):
    client.signature.full()
    _, kwargs = client._session.method.call_args

    assert kwargs == {
        "cookies": {"cookie1": True, "cookie2": True},
        "body": {"body1": True, "body2": True},
        "files": {"file1": b"1", "file2": b"1"},
        "headers": {"header1": True, "header2": True},
        "kwarg1": True,
        "kwarg2": True,
        "params": {"param1": True, "param2": True},
        "paths": {
            "path1": "path1",
            "path2": "path2",
        },
    }

    make_request = mocker.patch.object(BaseTestClient, "make_request")

    client.signature.full(test_mode=True, raise_exceptions=False)
    _, kwargs = make_request.call_args

    assert kwargs["extras"] == {
        "extra1": True,
        "extra2": True,
    }
    assert kwargs["kwargs"]["paths"] == {
        "path1": "path1",
        "path2": "path2",
    }
    assert kwargs["test_mode"] is True
    assert kwargs["raise_exceptions"] is False


def test_signature_unpacked_kwargs(client, mocker):
    with pytest.raises(
        ValidationError,
        check=lambda exc: len(exc.errors()) == 2
        and exc.errors()[0]["loc"] == ("required_param",)
        and exc.errors()[1]["loc"] == ("required_param_without_annotation",),
    ):
        client.signature.unpacked_kwargs(
            required_function_param=True,
            required_pydantic_function_body=ModelForTest(attr1=True, attr2=True),
            required_pydantic_body=ModelForTest(attr1=True, attr2=True),
            required_pydantic_extra=ModelForTest(attr1=True, attr2=True),
        )

    kwargs = dict(
        required_pydantic_function_body=ModelForTest(attr1=True, attr2=True),
        required_pydantic_body=ModelForTest(attr1=True, attr2=True),
        required_pydantic_extra=ModelForTest(attr1=True, attr2=True),
        required_function_param=True,
        required_param=True,
        required_param_without_annotation=True,
        extra1=True,
        kwarg1=True,
        cookies={"foo": "foo"},
        raise_exceptions=True,
    )

    client.signature.unpacked_kwargs(**kwargs)
    _, _kwargs = client._session.method.call_args

    assert _kwargs == {
        "cookies": {"foo": "foo"},
        "body": {
            "not_required_body_with_default": True,
            "not_required_function_body": True,
            "required_pydantic_body": {
                "attr1": True,
                "attr2": True,
            },
            "required_pydantic_function_body": {
                "attr1": True,
                "attr2": True,
            },
        },
        "kwarg1": True,
        "params": {
            "required_function_param": True,
            "required_param": True,
            "required_param_without_annotation": True,
        },
    }

    make_request = mocker.patch.object(BaseTestClient, "make_request")

    client.signature.unpacked_kwargs(**kwargs)
    _, _kwargs = make_request.call_args

    assert _kwargs["extras"]["required_pydantic_extra"] == ModelForTest(attr1=True, attr2=True)
    assert _kwargs["extras"]["extra1"] is True
    assert _kwargs["raise_exceptions"] is True


def test_client_method_not_set_in_context(client, mocker):
    mocker.patch.object(BaseTestClient, "context", new={"method": None})
    with pytest.raises(ValueError, match="Request context for is not setting."):
        # noinspection PyStatementEffect
        client.method


def test_get_extras(client, mocker):
    extras = {"extra1": True}
    mocker.patch.object(BaseTestClient, "context", new={"extras": extras})
    assert client.extras == extras


def test_success_method_validator(client):
    assert client.validated.get_success_validated_data()


def test_failure_method_validator(client, mocker):
    mocker.patch.object(client, "__expected_exceptions__", new=(ExceptionModel, ZeroDivisionError))

    with pytest.raises(ZeroDivisionError):
        assert client.validated.get_failure_validated_data()


@pytest.mark.parametrize(
    "max_retries,function",
    [
        (0, "_prepare_request_kwargs"),
        (1, "_prepare_request_kwargs"),
        (2, "_prepare_request_kwargs"),
        (0, "_finalize_response"),
        (1, "_finalize_response"),
        (2, "_finalize_response"),
    ],
    ids=[
        "no_retries_in_request_part",
        "one_retry_in_request_part",
        "two_retries_in_request_part",
        "no_retries_in_response_part",
        "one_retry_in_response_part",
        "two_retries_in_response_part",
    ],
)
def test_retry_request(client, mocker, max_retries, function):
    calls = 0

    def _new_function(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        client._retry_request()

    mocker.patch("pydantic.main._check_frozen")
    mocker.patch.object(client, function, new=_new_function)
    mocker.patch.object(client._settings, "max_retry_count", new=max_retries)

    with pytest.raises(
        MaxRetriesSDKException,
        match="The maximum number of requests retries for get_success_validated_data has been exceeded.*",
    ):
        assert client.validated.get_success_validated_data()
    assert calls == max_retries + 1


@pytest.mark.parametrize("max_retries", [0, 1, 2])
def test_retry_request_after_disconnect(client, mocker, max_retries):
    class DisconnectException(Exception): ...

    calls = 0

    def _new_check_disconnected_exception(exc: UnexpectedSDKException):
        if isinstance(exc.__context__, DisconnectException):
            return
        raise exc

    def _new_get(*_args, **_kwargs):
        nonlocal calls
        calls += 1

        raise DisconnectException

    mocker.patch("pydantic.main._check_frozen")
    mocker.patch.object(client._session, "method", new=_new_get)
    mocker.patch.object(client._settings, "max_retry_count_after_disconnect", new=max_retries)
    mocker.patch.object(client, "_check_disconnected_exception", new=_new_check_disconnected_exception)

    with pytest.raises(
        MaxRetriesAfterDisconnectSDKException,
        match="The maximum number of requests retries after disconnect for get_success_validated_data has been exceeded.*",
    ):
        assert client.validated.get_success_validated_data()

    assert calls == max_retries + 1


def test_context_not_applied():
    with pytest.raises(ValueError, match="Attribute __context__ value must be set."):
        # noinspection PyUnusedLocal
        class FooClient(BaseClient, ABC): ...


def test_set_context_already_applied():
    with pytest.raises(ValueError, match="Context already applied in one of base classes"):
        # noinspection PyUnusedLocal
        class FooClient(BaseTestClient, __context__=SimpleContext()): ...


def test_no_base_service_client():
    with pytest.raises(AttributeError, match="Attribute __base_service__ is required.*"):
        # noinspection PyAbstractClass,PyUnusedLocal
        class _Client(BaseClient, __context__=SimpleContext()): ...


def test_no_default_settings_client():
    with pytest.raises(AttributeError, match="Attribute __default_settings_class__ is required.*"):
        # noinspection PyAbstractClass,PyClassVar,PyUnusedLocal
        class _Client(BaseClient, __context__=SimpleContext()):
            __base_service__ = None  # type: ignore


def test_context_is_none(client, mocker):
    mocker.patch.object(client, "__context__", new=None)

    with pytest.raises(AttributeError, match="Attribute __context__ must be set."):
        # noinspection PyStatementEffect
        client.context


def test_inheritance_service_in_client():
    class InheritanceClient(BaseTestClient): ...

    class AdditionalService(BaseTestClientService):
        @OthersService.check_settings
        def method(self) -> BaseTestResponse: ...

    class DeepInheritanceClient(BaseTestClient):
        additional: AdditionalService

    assert InheritanceClient.__services__ == BaseTestClient.__services__
    assert DeepInheritanceClient.__services__ == {"additional": AdditionalService, **BaseTestClient.__services__}


def test_client_service_string_annotation():
    class FooClientService(BaseTestClientService): ...

    class InheritanceClient(BaseTestClient):
        foo: "FooClientService"

    assert BaseTestClientService.__registered_subclasses__["FooClientService"] is FooClientService
    assert InheritanceClient.__services__["foo"] is FooClientService
    assert isinstance(InheritanceClient().foo, FooClientService)


def test_client_service_duplicate_name():
    with pytest.raises(
        TypeError, match="Class name FooClientService already registered in .*.__registered_subclasses__"
    ):
        # noinspection PyUnusedLocal
        class FooClientService(BaseTestClientService): ...  # pyright: ignore [reportRedeclaration]

        # noinspection PyUnusedLocal,PyRedeclaration
        class FooClientService(BaseTestClientService): ...


def test_client_with_need_authentication(mocker):
    authenticate = mocker.patch.object(BaseTestClient, "_authenticate")
    client = BaseTestClient(settings=Settings(need_authentication=True))
    client.__init_session__()
    assert authenticate.call_count == 1


@pytest.mark.parametrize(
    "token_type,token,value",
    [
        ((TokenType.CUSTOM, "Foo"), "foo", "Foo foo"),
        ((TokenType.CUSTOM, None), "foo", "foo"),
        ((TokenType.BEARER, None), "foo", f"{TokenType.BEARER.value} foo"),
        ((TokenType.TOKEN, None), "foo", f"{TokenType.TOKEN.value} foo"),
        ((None, None), "foo", "foo"),
    ],
)
def test_authorization_token(token_type, token, value):
    token_type, custom_token_type = token_type

    client = BaseTestClient(settings=Settings(token_type=token_type, custom_token_type=custom_token_type, token=token))
    # noinspection PyProtectedMember
    assert client._authorization_token == value


_main_logger_name = "__main__"
_main_logger = logging.getLogger(_main_logger_name)
_other_logger_name = "__other__"
_other_logger = logging.getLogger(_other_logger_name)
_call_logger_name = "__call__"
_call_logger = logging.getLogger(_call_logger_name)


@pytest.mark.parametrize(
    "logger,settings,expected",
    [
        (_main_logger, None, _main_logger),
        (_main_logger_name, None, _main_logger),
        (None, Settings(default_logger=_main_logger), _main_logger),
        (None, Settings(default_logger_name=_main_logger_name), _main_logger),
        (None, Settings(use_logging_as_default_logger=True), logging),
        (None, Settings(use_logging_as_default_logger=False), None),
        # override priority
        (
            None,
            Settings(use_logging_as_default_logger=True, default_logger_name=_other_logger_name),
            _other_logger,
        ),
        (None, Settings(default_logger_name=_main_logger_name, default_logger=_other_logger), _other_logger),
        (_other_logger_name, Settings(default_logger=_main_logger), _other_logger),
        (_other_logger, Settings(default_logger=_main_logger), _other_logger),
    ],
    ids=[
        "logger_in_call",
        "logger_name_in_call",
        "logger_in_settings",
        "logger_name_in_settings",
        "use_logging_as_default_logger",
        "not_use_logging_as_default_logger",
        "logger_name_in_settings_gt_use_logging_as_default_logger",
        "logger_in_settings_gt_logger_name_in_settings",
        "logger_name_in_call_gt_logger_in_settings",
        "logger_in_call_call_gt_logger_in_settings",
    ],
)
def test_set_logger(caplog, logger, settings, expected):
    client = BaseTestClient(logger=logger, settings=settings)
    assert client._logger == expected

    if not client._logger:
        with caplog.at_level(logging.ERROR):
            client.logging(message="Error message")
            assert "[BaseTestClient]: Error message" not in caplog.text

        return

    logger_name = client._logger.name if isinstance(client._logger, logging.Logger) else "root"

    with caplog.at_level(logging.ERROR):
        client.logging(message="Error message")
        assert "[BaseTestClient]: Error message" in caplog.text
        assert logger_name in caplog.text

    with caplog.at_level(logging.ERROR):
        client.logging(message="Error message", method=OthersService.signature)  # pyright: ignore [reportArgumentType)]
        assert "[BaseTestClient][signature]: Error message" in caplog.text
        assert logger_name in caplog.text

    with caplog.at_level(logging.DEBUG):
        client.logging(message="Debug message", level=LogLevel.DEBUG)
        assert "[BaseTestClient]: Debug message" in caplog.text
        assert logger_name in caplog.text

    with caplog.at_level(logging.ERROR):
        client.logging(message="Error message", logger=_call_logger_name)
        assert "[BaseTestClient]: Error message" in caplog.text
        assert _call_logger_name in caplog.text

    with caplog.at_level(logging.ERROR):
        client.logging(message="Error message", logger=_call_logger)
        assert "[BaseTestClient]: Error message" in caplog.text
        assert _call_logger_name in caplog.text


@pytest.mark.parametrize(
    "method,response_type",
    [
        ("_make_request_error_response", BaseTestRequestErrorResponse),
        ("_make_response_error_response", BaseTestResponseErrorResponse),
        ("_make_retry_error_response", BaseTestRetryErrorResponse),
    ],
    ids=[
        "request",
        "prepare",
        "retry",
    ],
)
def test_make_error_response(client, method, response_type):
    assert isinstance(getattr(client, method)(), response_type)


def test_get_fake_response(client, mocker):
    default_value = {"attr": 1}
    default_factory_return_value = {"attr": 1}
    method_factory_return_value = {"attr": 1}

    mocker.patch.object(BaseTestClient, "method", new=OthersService.signature)

    assert client._get_fake_response() is None

    mocker.patch.object(client, "__default_test_response__", new=default_value)

    assert client._get_fake_response() == default_value

    mocker.patch.object(client.__class__, "__default_test_response_factory__", new=lambda: default_factory_return_value)

    assert client._get_fake_response() == default_factory_return_value

    class ModelWithFactory(ProxyModel):
        class _Factory:
            @classmethod
            def build(cls):
                return method_factory_return_value

        __factory__ = _Factory

    mocker.patch.object(OthersService.signature, "response_type", new=ModelWithFactory)

    assert client._get_fake_response() == method_factory_return_value


@pytest.mark.parametrize(
    "setting",
    [
        "raise_exceptions",
        "test_mode",
        "skip_for_test",
        "fake_for_test",
        "max_retry_count",
        "max_retry_count_after_disconnect",
    ],
)
def test_make_request_settings(client, mocker, setting):
    @dataclass
    class RequestContext:
        value: dict

    mocker.patch("pydantic.main._check_frozen")
    mocker.patch.object(client, "__context__", new=RequestContext({}))
    mocker.patch.object(client._settings, setting, new=False)
    client.settings.check_settings()
    assert client.context[setting] is False  # type: ignore

    client.settings.check_settings(**{setting: True})
    assert client.context[setting] is True  # type: ignore


def test_skip_for_test(client):
    assert client.settings.check_settings(test_mode=True, skip_for_test=True) is None


def test_fake_for_test(client):
    assert client.settings.check_settings(test_mode=True, fake_for_test=True) is None


def test_not_raise_max_retries_exceptions(client, mocker):
    def _new_make_url(*_args, **_kwargs):
        client._retry_request()

    mocker.patch.object(client, "_prepare_request_kwargs", new=_new_make_url)

    response = client.settings.check_settings(raise_exceptions=False)
    assert isinstance(response, BaseTestRetryErrorResponse)


@pytest.mark.parametrize(
    "function,exc,response_type",
    [
        ("_prepare_request_kwargs", FailureRequestSDKException, BaseTestRequestErrorResponse),
        ("_prepare_request_kwargs", ZeroDivisionError, BaseTestRequestErrorResponse),
        ("_finalize_response", FailureRequestSDKException, BaseTestResponseErrorResponse),
        ("_finalize_response", ZeroDivisionError, BaseTestResponseErrorResponse),
    ],
    ids=[
        "expected_in_request_part",
        "unexpected_in_request_part",
        "expected_in_response_part",
        "unexpected_in_response_part",
    ],
)
def test_not_raise_exceptions(client, mocker, function, exc, response_type):
    def _new_function(*_args, **_kwargs):
        raise exc

    mocker.patch.object(client, function, new=_new_function)

    response = client.settings.check_settings(raise_exceptions=False)
    assert isinstance(response, response_type)


@pytest.mark.parametrize(
    "function,raised_exception,expected_exception",
    [
        ("_prepare_request_kwargs", FailureRequestSDKException, FailureRequestSDKException),
        ("_validate_raw_response", FailureRequestSDKException, FailureRequestSDKException),
        ("_prepare_request_kwargs", ZeroDivisionError, UnexpectedSDKException),
        ("_validate_raw_response", ZeroDivisionError, UnexpectedSDKException),
    ],
    ids=[
        "expected_exception_in_request_part",
        "expected_exception_in_response_part",
        "unexpected_exception_in_request_part",
        "unexpected_exception_in_response_part",
    ],
)
def test_raise_exceptions(client, mocker, function, raised_exception, expected_exception):
    def _raise_expected_exception(*_args, **_kwargs):
        raise raised_exception

    mocker.patch.object(client, function, new=_raise_expected_exception)

    with pytest.raises(expected_exception):
        client.validated.get_success_validated_data()
