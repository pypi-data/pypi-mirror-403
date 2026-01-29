"""Module with fields for rest backends."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Literal, TypedDict, TypeVar

from pydantic import AliasChoices, AliasPath, Discriminator

# noinspection PyProtectedMember
from pydantic.fields import FieldInfo, _FromFieldInfoInputs
from pydantic_core import PydanticUndefined
from typing_extensions import Unpack

from web_sdk.enums import HTTPMethod

if TYPE_CHECKING:
    from collections.abc import Callable
    from re import Pattern

    import annotated_types

    # noinspection PyProtectedMember
    import pydantic.fields

    # noinspection PyProtectedMember
    from pydantic.config import JsonDict

    from web_sdk.types import PartsNames

    class _SDKFieldKwargs(TypedDict, total=False):
        default_factory: Callable[[], Any] | None
        alias: str | None
        alias_priority: int | None
        validation_alias: str | AliasPath | AliasChoices | None
        title: str | None
        field_title_generator: Callable[[str, pydantic.fields.FieldInfo], str] | None
        description: str | None
        examples: list[Any] | None
        exclude: bool | None
        discriminator: str | Discriminator | None
        deprecated: pydantic.fields.Deprecated | str | bool | None
        json_schema_extra: JsonDict | Callable[[JsonDict], None] | None
        frozen: bool | None
        validate_default: bool | None
        repr: bool
        init: bool | None
        init_var: bool | None
        kw_only: bool | None
        pattern: str | Pattern[str] | None
        strict: bool | None
        coerce_numbers_to_str: bool | None
        gt: annotated_types.SupportsGt | None
        ge: annotated_types.SupportsGe | None
        lt: annotated_types.SupportsLt | None
        le: annotated_types.SupportsLe | None
        multiple_of: float | None
        allow_inf_nan: bool | None
        max_digits: int | None
        decimal_places: int | None
        min_length: int | None
        max_length: int | None
        union_mode: Literal["smart", "left_to_right"]
        fail_fast: bool | None


_Unset: Any = PydanticUndefined

_T = TypeVar("_T")


def _request_field(field_class: type[RequestFieldInfo]):
    def __request_field(default: Any = PydanticUndefined, **kwargs: Unpack[_SDKFieldKwargs]) -> RequestFieldInfo:
        # Here we replace serialization_alias with alias because we are only getting the data.
        serialization_alias = kwargs.get("alias", _Unset)
        kwargs["alias"] = _Unset

        # This part rewrite from pydantic.Field without serialization_alias preparing and alias replacing
        validation_alias = kwargs.get("validation_alias")
        if (
            validation_alias
            and validation_alias is not _Unset
            and not isinstance(validation_alias, (str, AliasChoices, AliasPath))
        ):
            raise TypeError("Invalid `validation_alias` type. it should be `str`, `AliasChoices`, or `AliasPath`")

        return field_class.from_field(default, serialization_alias=serialization_alias, **kwargs)

    # set attr for getting in RequestParts.get_field_info
    __request_field.__create_default_field_info__ = lambda: __request_field()  # type: ignore

    return __request_field


class RequestFieldInfo(FieldInfo):  # type: ignore
    """Base class for request field info."""

    __parts_mapping__: ClassVar[dict[PartsNames, type[RequestFieldInfo]]] = {}
    __methods_defaults__: ClassVar[dict[HTTPMethod, type[RequestFieldInfo]]] = {}

    part_name: ClassVar[PartsNames]

    field_mode: ClassVar[Literal["json", "python", "no_deep"] | str] = "json"
    default_for_methods: ClassVar[tuple[HTTPMethod, ...]] = ()

    def __init_subclass__(cls, **kwargs):
        """Registry subclasses."""
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "part_name"):
            raise AttributeError(f"Field `part_name` is not defined for {cls}")

        # register cls in parts mapping
        if cls.part_name in RequestFieldInfo.__parts_mapping__:
            warnings.warn(
                f"{RequestFieldInfo} subclass for part {cls.part_name} already exists. "
                f"Class {cls} will overwrite the value in __parts_mapping__",
                stacklevel=2,
                category=UserWarning,
            )
        RequestFieldInfo.__parts_mapping__[cls.part_name] = cls

        # register cls in methods defaults mapping
        for method in cls.default_for_methods:
            if method in cls.__methods_defaults__:
                warnings.warn(
                    f"Subclass {RequestFieldInfo} specifies {method} in __default_for_methods__, "
                    f"but the {method} method already exists in __methods_defaults__."
                    f"Class {cls} will overwrite the value in __methods_defaults__",
                    stacklevel=2,
                    category=UserWarning,
                )
            RequestFieldInfo.__methods_defaults__[method] = cls

    @classmethod
    def from_field(  # pyright: ignore[reportIncompatibleMethodOverride]
        cls,
        default: Any = PydanticUndefined,
        **kwargs: Unpack[_FromFieldInfoInputs],
    ) -> RequestFieldInfo:
        """Change staticmethod on classmethod."""
        return cls(default=default, **kwargs)


class PathFieldInfo(RequestFieldInfo):  # type: ignore[misc]
    """FieldInfo for path part."""

    part_name = "paths"


class BodyFieldInfo(RequestFieldInfo):  # type: ignore[misc]
    """FieldInfo for body part."""

    part_name = "body"
    default_for_methods = (HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH)


class HeaderFieldInfo(RequestFieldInfo):  # type: ignore[misc]
    """FieldInfo for header part."""

    part_name = "headers"


class ParamFieldInfo(RequestFieldInfo):  # type: ignore[misc]
    """FieldInfo for param part."""

    part_name = "params"
    default_for_methods = (HTTPMethod.GET, HTTPMethod.DELETE, HTTPMethod.HEAD, HTTPMethod.OPTIONS)


class FileFieldInfo(RequestFieldInfo):  # type: ignore[misc]
    """FieldInfo for file part."""

    field_mode = "no_deep"
    part_name = "files"


class CookieFieldInfo(RequestFieldInfo):  # type: ignore[misc]
    """FieldInfo for coolie part."""

    part_name = "cookies"


class KwargFieldInfo(RequestFieldInfo):  # type: ignore[misc]
    """FieldInfo for request kwargs part."""

    part_name = "kwargs"


class ExtraFieldInfo(RequestFieldInfo):  # type: ignore[misc]
    """FieldInfo for extra kwargs part."""

    field_mode = "no_deep"
    part_name = "extras"


class SettingFieldInfo(RequestFieldInfo):  # type: ignore[misc]
    """FieldInfo for setting kwargs part."""

    field_mode = "python"
    part_name = "settings"


_FieldType = TypeVar("_FieldType", bound=RequestFieldInfo)


Path = _request_field(PathFieldInfo)
Body = _request_field(BodyFieldInfo)
Header = _request_field(HeaderFieldInfo)
Param = _request_field(ParamFieldInfo)
File = _request_field(FileFieldInfo)
Cookie = _request_field(CookieFieldInfo)
Kwarg = _request_field(KwargFieldInfo)
Extra = _request_field(ExtraFieldInfo)
Setting = _request_field(SettingFieldInfo)

APath = Annotated[_T, Path]
ABody = Annotated[_T, Body]
AHeader = Annotated[_T, Header]
AParam = Annotated[_T, Param]
AFile = Annotated[_T, File]
ACookie = Annotated[_T, Cookie]
AKwarg = Annotated[_T, Kwarg]
AExtra = Annotated[_T, Extra]
ASetting = Annotated[_T, Setting]
