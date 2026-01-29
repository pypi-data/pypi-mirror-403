"""Utils for request parsing."""

import inspect
from collections.abc import Callable
from functools import cached_property
from types import FunctionType
from typing import Any, ClassVar, Generic, TypeVar, cast

from pydantic import PrivateAttr, create_model
from pydantic.fields import Field, FieldInfo
from pydantic_core import PydanticUndefined
from typing_extensions import NotRequired, Required, TypedDict, Unpack, is_typeddict

from web_sdk.contrib.pydantic.models import PydanticModel
from web_sdk.core.fields import RequestFieldInfo
from web_sdk.core.kwargs import RequestSettingsKwargs
from web_sdk.types import PartsNames, TExtras, TKwargs
from web_sdk.utils.dicts import merge_dicts
from web_sdk.utils.inspect import get_params_with_values
from web_sdk.utils.statements import first

_TValue = TypeVar("_TValue")


# TODO: may be need make dynamic generation
class _RequestPartsBase(PydanticModel, Generic[_TValue]):
    paths: dict[str, _TValue] = Field(default_factory=dict)
    body: dict[str, _TValue] = Field(default_factory=dict)
    headers: dict[str, _TValue] = Field(default_factory=dict)
    params: dict[str, _TValue] = Field(default_factory=dict)
    files: dict[str, _TValue] = Field(default_factory=dict)
    cookies: dict[str, _TValue] = Field(default_factory=dict)
    kwargs: dict[str, _TValue] = Field(default_factory=dict)
    extras: dict[str, _TValue] = Field(default_factory=dict)
    settings: dict[str, _TValue] = Field(default_factory=dict)


class _RequestPartsDump(TypedDict, Generic[TKwargs, TExtras]):
    """Dump of request parts for function call."""

    kwargs: TKwargs
    extras: TExtras
    settings: RequestSettingsKwargs


class _RequestPartsValues(_RequestPartsBase[Any]):
    """Model for setting request parts values."""

    settings: RequestSettingsKwargs = Field(default_factory=RequestSettingsKwargs)  # type: ignore


class RequestParts(_RequestPartsBase[FieldInfo], Generic[TKwargs, TExtras]):
    """Model for request parts validation."""

    # TODO: We need something more reliable. Maby change annotation of callable
    #       on Callable[Concatenate[S, P], R] and just skip first parameter or something
    __ignored_params__: ClassVar[tuple[str, ...]] = ("self",)
    """Function params names, which will be ignored"""

    __request_parts_values__: ClassVar[type[_RequestPartsValues]] = _RequestPartsValues
    """Model for setting request parts values."""
    __parts_types_mapping__: ClassVar[dict[PartsNames, type[RequestFieldInfo]]] = RequestFieldInfo.__parts_mapping__
    """Mapping parts names with FieldInfo types"""
    __types_parts_mapping__: ClassVar[dict[type[FieldInfo], PartsNames]] = {
        value: key for key, value in __parts_types_mapping__.items()
    }
    """Reversed __parts_mapping__ mapping"""

    _fields: dict[str, FieldInfo] = PrivateAttr(default_factory=dict)
    """Dict of registered fields"""

    """Request method"""
    function: Callable
    """Function for request part creation"""

    @staticmethod
    def get_field_info(*items: RequestFieldInfo | FunctionType) -> RequestFieldInfo | None:
        """Get field info from items."""
        for item in items:
            if isinstance(item, FunctionType):
                # check attr setting in web_sdk.backend.rest.fields._request_field
                if create_default_field_info := getattr(item, "__create_default_field_info__", None):
                    return create_default_field_info()
            elif isinstance(item, RequestFieldInfo):
                return item
        return None

    @classmethod
    def _get_field_form_param(
        cls, param: inspect.Parameter, default_field_info: type[RequestFieldInfo]
    ) -> RequestFieldInfo:
        """Get field from function signature param.

        Args:
            param: Parameter from function signature
            default_field_info: default field info type

        Returns: field info instance

        """
        field: None | RequestFieldInfo = None
        annotation, default = param.annotation, param.default

        # this method works for annotated cases, if we have an annotation like (arg: Annotated[str, Body(...)])
        # we get the following: annotation.__metadata__ == (BodyFieldInfo, ) and annotation.__args__ == (str, )
        if metadata := getattr(annotation, "__metadata__", None):
            if field := cls.get_field_info(*metadata):
                annotation = first(annotation.__args__)
                if default != param.empty:
                    field.default = default

        # this case working when we have signature like (arg: bool = Body) or (arg: bool = Body(False))
        if _field := cls.get_field_info(default):
            field = _field

        # this case working for args, without Field like annotation or defaults (arg: int = None)
        if not field:
            field = default_field_info()
            if default != param.empty:
                field.default = default

        # set the FieldInfo annotation to correctly generate validator fields.
        field.annotation = annotation
        return field

    # noinspection PyTypedDict
    @classmethod
    def _get_fields_form_var_keyword_param(
        cls, param: inspect.Parameter, default_field_info: type[RequestFieldInfo]
    ) -> list[tuple[str, RequestFieldInfo]]:
        """Get field from function signature param.

        Args:
            param: VarKeyword Parameter from function signature
            default_field_info: default field info type

        Returns: tuple of fields names with fields infos instances

        """
        # if no annotation or not Unpack annotation or not _UnpackAlias
        if getattr(param.annotation, "__origin__", None) is not Unpack:
            raise TypeError(
                f"Annotation for var keyword '{param.name}' must be unpack with typing_extensions.TypedDict argument"
            )

        typed_dict = param.annotation.__args__[0]
        # if arg is not TypedDict raise exception
        if not is_typeddict(typed_dict):
            raise TypeError(f"Arg of var keyword '{param.name}' must be typing_extensions.TypedDict")

        result = []
        for name, annotation in typed_dict.__annotations__.items():
            field: None | RequestFieldInfo = None

            # unwrap annotation if it is Required or NotRequired
            if getattr(annotation, "__origin__", None) in (Required, NotRequired):
                annotation = annotation.__args__[0]

            # this method works for annotated cases, if we have an annotation like attr: Annotated[str, Body(...)]
            # we get the following: annotation.__metadata__ == (BodyFieldInfo, ) and annotation.__args__ == (str, )
            if metadata := getattr(annotation, "__metadata__", None):
                if field := cls.get_field_info(*metadata):
                    annotation = first(annotation.__args__)

            # this case working for attrs, without Field like annotation attr: int
            if not field:
                field = default_field_info()

            field.annotation = annotation

            # for Foo(TypedDict, total=False) and NotRequired if default not setting, set default = None
            if field.default is PydanticUndefined and name in typed_dict.__optional_keys__:
                field.default = None

            result.append((name, field))

        return result

    @classmethod
    def get_request_parts(
        cls, function: Callable, default_field_info: type[RequestFieldInfo]
    ) -> "RequestParts[TKwargs, TExtras]":
        """Set request parts for function.

        Args:
            function: function for request parts setting
            default_field_info: default field info type

        """
        # get all params from original function signature
        params = inspect.signature(inspect.unwrap(function)).parameters

        # create empty RequestParts instance
        request_parts = cls(function=function)

        # fill request parts from params by types
        for name, param in params.items():
            if name in cls.__ignored_params__:
                continue

            if param.kind == inspect.Parameter.VAR_KEYWORD:
                for _name, _field in cls._get_fields_form_var_keyword_param(param, default_field_info):
                    request_parts.add_param(_name, _field)
            else:
                # add param to RequestParts instance
                field = cls._get_field_form_param(param, default_field_info)
                request_parts.add_param(name, field)

        # let's access the validation_class attribute to get the cached value before calling the function.

        # noinspection PyStatementEffect
        request_parts.validation_class  # noqa

        return request_parts

    @staticmethod
    def _get_default(value: Any):
        """Get default value from default factory if value is FieldInfo.

        Args:
            value: Default value in original function signature

        Returns: default value from default factory if value is FieldInfo

        """
        return value.get_default(call_default_factory=True) if isinstance(value, FieldInfo) else value

    def _skip_part(self, part_name: PartsNames) -> bool:
        """Is need to skip part. Need for backends in which certain parts are missing for certain methods.

        Args:
            part_name: Part name

        Returns: need skip or not

        """
        return False

    def add_param(self, name: str, field: RequestFieldInfo):
        """Add param to request part.

        Args:
            name: Name of part
            field: FieldInfo instance

        """
        if name in self._fields:
            raise ValueError(f"Duplicate param name: {name}")

        part = self.__types_parts_mapping__.get(field.__class__)
        if not part:
            raise ValueError(f"Unsupported field type: {field.__class__}")

        self._fields[name] = field
        getattr(self, part)[name] = field

    def dump_request_parts(self, *args, **kwargs) -> _RequestPartsDump[TKwargs, TExtras]:
        """Get all request parts."""
        # get dict of values for every param in request part fields
        data = get_params_with_values(
            self.function, list(self.fields.keys()), *args, **kwargs, __skip_params_errors__=True
        )
        # get all data with default values if no value were passed
        dict_data = {key: self._get_default(value) for key, value in data.items()}
        # validate data with RequestPrats instance validator
        validated_data = self.validation_class.model_validate(dict_data, from_attributes=True)

        # get request parts values instance for setting serialized values
        request_parts = self.__request_parts_values__()

        for part_name in self.__parts_types_mapping__:
            # for backends in which certain parts are missing for certain methods
            if self._skip_part(part_name):
                continue

            field_info_type = self.__parts_types_mapping__[part_name]
            part_params = getattr(self, part_name).keys()

            if field_info_type.field_mode == "no_deep":
                # getting first level dict only
                data = {
                    # get key from alias or field_name
                    self.validation_class.model_fields[key].serialization_alias or key: value
                    # iter by validated_data fields
                    for key, value in validated_data.__dict__.items()
                    # exclude None values and include only current part keys
                    if value is not None and key in part_params
                }
                setattr(request_parts, part_name, data)
                continue

            # dump kwargs
            dump_kwargs = dict(
                # only part params
                include=part_params,
                # TODO: may be this param must be changeable
                exclude_none=True,
                # for same names in different parts we use alias
                by_alias=True,
                # serialization mode from FieldInfo
                mode=field_info_type.field_mode,
            )
            # set serialized data to request part by part name
            setattr(request_parts, part_name, validated_data.model_dump(**dump_kwargs))

        # merge request_parts with kwargs override
        kwargs = cast(
            "TKwargs",
            merge_dicts(
                # request kwargs from different parts, don't use model_dump for supporting no_deep mode
                {
                    key: value
                    for key, value in request_parts.__dict__.items()
                    if value and key not in ("extras", "settings", "kwargs")
                },
                # override kwargs from KwargFieldInfo
                request_parts.kwargs,
            ),
        )
        extras = cast("TExtras", request_parts.extras or {})

        # return data separated by types
        return _RequestPartsDump[TKwargs, TExtras](
            kwargs=kwargs,
            extras=extras,
            settings=request_parts.settings,
        )

    @cached_property
    def validation_class(self):
        """Create validation class by expected fields."""
        return create_model(
            "_ValidationClass",
            __base__=PydanticModel,
            # Here the linter thinks that everything is bad because the keys are not explicitly specified
            **{name: (field.annotation, field) for name, field in self.fields.items()},  # type: ignore
        )

    @property
    def fields(self):
        """Return registered fields."""
        return self._fields
