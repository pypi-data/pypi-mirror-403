"""Interfaces of this module."""

__all__ = [
    "IClient",
    "IMethod",
    "IService",
]

from .clients import IClient
from .methods import IMethod
from .services import IService
