"""Custom pydantic.BaseModel."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, ModelWrapValidatorHandler, model_validator

# noinspection PyProtectedMember
from pydantic._internal._model_construction import (
    ModelMetaclass,
    NoInitField,
    PydanticModelField,  # pyright: ignore
    PydanticModelPrivateAttr,  # pyright: ignore
)
from pydantic.fields import PrivateAttr
from typing_extensions import Self, dataclass_transform

from web_sdk.utils.annotations import signature_from


class PydanticIgnore:
    """Base class for create ignored descriptors for pydantic."""


class PydanticModel(BaseModel):
    """Base custom pydantic model."""

    model_config = ConfigDict(
        coerce_numbers_to_str=True,
        arbitrary_types_allowed=True,
        validate_default=True,
        ignored_types=(PydanticIgnore,),
    )


# Some magic for avoid wrong pydantic attrs highlights for proxy model
class ProxyModelMeta(ModelMetaclass):  # pyright: ignore [reportRedeclaration]
    """Metaclass for proxy model class."""


if TYPE_CHECKING:
    ProxyModelMeta: type[ProxyModelMeta]  # type: ignore
else:
    _dataclass_transform = dataclass_transform(
        kw_only_default=True,
        field_specifiers=(PydanticModelField, PydanticModelPrivateAttr, NoInitField),
    )

    ProxyModelMeta: type[ProxyModelMeta] = _dataclass_transform(ProxyModelMeta)


class ProxyModel(PydanticModel, metaclass=ProxyModelMeta):  # pyright: ignore
    """Custom metaclass for pydantic.BaseModel."""

    __original_object__: Any = PydanticIgnore()
    _extra_data: dict = PrivateAttr(default_factory=dict)

    def __init__(self, /, **kwargs):
        """__init__ override."""
        extra_data = {}
        for key in list(kwargs):
            if key not in self.__class__.model_fields:
                extra_data[key] = kwargs.pop(key)

        super().__init__(**kwargs)
        self.extra_data = extra_data

    def __getattr__(self, item):
        """__getattr__ override."""
        try:
            return super().__getattr__(item)  # type: ignore
        except AttributeError:
            try:
                return self.extra_data[item]
            except KeyError:
                return getattr(self.original_object, item)

    def __setattr__(self, name, value):
        """__setattr__ override."""
        try:
            super().__setattr__(name, value)
        except (AttributeError, ValueError):
            self.extra_data[name] = value

    # TODO: extend representation functions

    @property
    def extra_data(self):
        """Additional data, getting during initialization."""
        return self._extra_data

    @extra_data.setter
    def extra_data(self, value):
        """Set additional data, got during initialization."""
        self._extra_data = value

    @property
    def original_object(self):
        """Original object set during model_validate call."""
        return self.__original_object__

    @original_object.setter
    def original_object(self, value):
        """Set original object."""
        self.__original_object__ = value

    @model_validator(mode="wrap")
    @classmethod
    def save_original(cls, data: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        """Save original object."""
        validated_self = handler(data)
        validated_self.original_object = data
        return validated_self

    @signature_from(BaseModel.model_dump)
    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Generate a dictionary representation of the model, optionally specifying which fields to include or exclude."""
        # TODO: include support
        data = super().model_dump(**kwargs)

        extra_data = self.extra_data
        if exclude := kwargs.get("exclude"):
            extra_data = {k: v for k, v in extra_data.items() if k not in exclude}
        data = {**extra_data, **data}

        return data
