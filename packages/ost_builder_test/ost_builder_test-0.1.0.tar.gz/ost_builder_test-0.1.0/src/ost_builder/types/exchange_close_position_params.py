# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ExchangeClosePositionParams", "Close"]


class ExchangeClosePositionParams(TypedDict, total=False):
    closes: Required[Iterable[Close]]
    """Positions to build close transactions for"""

    sp: float
    """Slippage percentage (0-100)"""

    x_request_id: Annotated[str, PropertyInfo(alias="X-Request-ID")]


class Close(TypedDict, total=False):
    a: Required[int]
    """Pair index"""

    p: Required[str]
    """Current market price"""

    r: Required[float]
    """Close percentage (1-100)"""

    t: Required[int]
    """Trade index"""
