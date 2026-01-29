from typing import Any

from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.core.bases import BaseService
from web_sdk.core.bases.rest.methods import RestMethod
from web_sdk.enums import HTTPMethod

# noinspection PyProtectedMember
from web_sdk.types import TResponse

from .types import Extras, Kwargs


class Service(BaseService[Kwargs, Extras]): ...


class Method(RestMethod[TResponse, Kwargs, Extras]): ...


class ExtrasService(Service, path="extras", extras=Extras(extra1=True)):
    get = Method[dict](
        method=HTTPMethod.GET,
        extras=Extras(extra2=True),
    )


def _test_validate(is_success: bool):
    def _validator(_: Any):
        if is_success:
            return True
        raise ZeroDivisionError

    return _validator


class OthersService(Service, path=""):
    signature = Method[PydanticModel](path="signature")
    full_signature = Method[PydanticModel](path="signature/{path1}/{path2}")
    get_success_validated_data = Method[PydanticModel]("validated_data", validator=_test_validate(True))
    get_failure_validated_data = Method[PydanticModel]("validated_data", validator=_test_validate(False))
    check_settings = Method[PydanticModel](path="check-settings")
