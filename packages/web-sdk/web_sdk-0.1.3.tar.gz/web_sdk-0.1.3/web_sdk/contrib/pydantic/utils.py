"""Pydantic utils."""

from typing import Any, Literal

from pydantic import TypeAdapter
from typing_extensions import overload

from web_sdk.types import T


@overload
def convert(
    to_type: T,
    obj: str | bytes | bytearray,
    *,
    strict: bool | None = None,
    from_attributes: bool | None = None,
    context: dict[str, Any] | None = None,
    mode: Literal["json"] = "json",
) -> T: ...
@overload
def convert(
    to_type: T,
    obj: Any,
    *,
    strict: bool | None = None,
    from_attributes: bool | None = None,
    context: dict[str, Any] | None = None,
    mode: Literal["python", "json", "string"] = "python",
) -> T: ...
def convert(
    to_type: T,
    obj: Any,
    *,
    strict: bool | None = None,
    from_attributes: bool | None = None,
    context: dict[str, Any] | None = None,
    mode: Literal["python", "json", "string"] = "python",
) -> T:
    """Convert object to type.

    Args:
        to_type: Target type
        obj: Original object
        strict: Следует ли строго соблюдать типы
        from_attributes: Получать значения из атрибутов
        context: Контекст
        mode: Тип преобразования

    Returns: Target type instance

    """
    adapter = TypeAdapter(to_type)
    if mode == "python":
        return adapter.validate_python(obj, from_attributes=from_attributes, strict=strict, context=context)
    elif mode == "json":
        return adapter.validate_json(obj, strict=strict, context=context)
    elif mode == "string":
        return adapter.validate_strings(obj, strict=strict, context=context)
    raise ValueError(f"Unsupported mode: {mode}. Expected one of 'python', 'json', 'string'")
