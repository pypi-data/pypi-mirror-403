# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ExchangeModifyOrderParams"]


class ExchangeModifyOrderParams(TypedDict, total=False):
    a: Required[int]
    """Pair index"""

    i: Required[int]
    """Limit order index (if p provided) or trade index (if updating TP/SL)"""

    p: str
    """New limit order trigger price (omit to update open trade TP/SL)"""

    sl: str
    """New stop loss price ("0" = reset to default)"""

    tp: str
    """New take profit price ("0" = reset to default)"""

    x_request_id: Annotated[str, PropertyInfo(alias="X-Request-ID")]
