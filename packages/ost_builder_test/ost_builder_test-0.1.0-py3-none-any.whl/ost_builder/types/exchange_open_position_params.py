# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ExchangeOpenPositionParams", "Order", "Bd"]


class ExchangeOpenPositionParams(TypedDict, total=False):
    orders: Required[Iterable[Order]]
    """Orders to build transactions for"""

    bd: Bd
    """Builder fee configuration for integrators"""

    sp: float
    """Slippage percentage for market orders (0-100)"""

    x_request_id: Annotated[str, PropertyInfo(alias="X-Request-ID")]


class Order(TypedDict, total=False):
    a: Required[int]
    """Pair index"""

    b: Required[bool]
    """Direction (true = long, false = short)"""

    l: Required[str]
    """Leverage (e.g., "10" for 10x)"""

    p: Required[str]
    """Price (e.g., "42500.00")"""

    s: Required[str]
    """Collateral in USD (minimum 5)"""

    t: Required[Literal["market", "limit", "stop"]]
    """Order type"""

    sl: str
    """Stop loss price ("0" = default liquidation price)"""

    tp: str
    """Take profit price ("0" = default openPrice + 900%)"""


class Bd(TypedDict, total=False):
    """Builder fee configuration for integrators"""

    b: Required[str]
    """Builder address (0x...)"""

    f: Required[float]
    """Fee percentage (max 0.5%)"""
