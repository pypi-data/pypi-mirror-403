# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ExchangeModifyOrderResponse", "Transaction"]


class Transaction(BaseModel):
    data: str
    """ABI-encoded calldata"""

    to: str
    """Contract address"""

    value: str
    """ETH value (usually "0")"""

    from_: Optional[str] = FieldInfo(alias="from", default=None)
    """Trader address"""


class ExchangeModifyOrderResponse(BaseModel):
    transactions: List[Transaction]
