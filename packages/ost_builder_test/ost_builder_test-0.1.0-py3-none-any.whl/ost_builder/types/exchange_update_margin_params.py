# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ExchangeUpdateMarginParams"]


class ExchangeUpdateMarginParams(TypedDict, total=False):
    a: Required[int]
    """Pair index"""

    amount: Required[str]
    """USD amount: positive = add, negative = remove"""

    i: Required[int]
    """Trade index"""

    x_request_id: Annotated[str, PropertyInfo(alias="X-Request-ID")]
