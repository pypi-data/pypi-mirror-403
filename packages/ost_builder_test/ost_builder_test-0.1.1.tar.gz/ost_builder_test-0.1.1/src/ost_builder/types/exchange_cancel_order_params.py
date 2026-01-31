# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ExchangeCancelOrderParams", "Cancel"]


class ExchangeCancelOrderParams(TypedDict, total=False):
    cancels: Required[Iterable[Cancel]]
    """Orders to build cancel transactions for"""

    x_request_id: Annotated[str, PropertyInfo(alias="X-Request-ID")]


class Cancel(TypedDict, total=False):
    t: Required[Literal["limit", "close", "open"]]
    """Cancel type: limit (requires a, i), close/open (requires o)"""

    a: int
    """Pair index (for limit cancel)"""

    i: int
    """Order index (for limit cancel)"""

    o: int
    """Order ID (for close/open timeout cancel)"""
