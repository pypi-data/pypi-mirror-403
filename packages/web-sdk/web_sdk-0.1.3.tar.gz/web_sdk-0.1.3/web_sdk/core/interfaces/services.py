"""Interfaces for services."""

from __future__ import annotations

from abc import ABC
from typing import Generic

from web_sdk.types import TExtras, TKwargs


class IService(Generic[TKwargs, TExtras], ABC):
    """Service interface."""

    path: str
    """Path part in url or service name"""
    kwargs: TKwargs
    """Make request kwargs"""
    extras: TExtras
    """Extra kwargs"""
    description: str | None
    """Service description"""
