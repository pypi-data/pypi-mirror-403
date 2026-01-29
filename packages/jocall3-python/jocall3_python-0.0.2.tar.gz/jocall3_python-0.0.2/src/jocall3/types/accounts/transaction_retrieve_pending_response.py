# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime
from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["TransactionRetrievePendingResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)

    ai_category_confidence: Optional[float] = FieldInfo(alias="aiCategoryConfidence", default=None)

    amount: Optional[float] = None

    carbon_footprint: Optional[float] = FieldInfo(alias="carbonFootprint", default=None)

    category: Optional[str] = None

    currency: Optional[str] = None

    date: Optional[datetime.date] = None

    description: Optional[str] = None

    dispute_status: Optional[str] = FieldInfo(alias="disputeStatus", default=None)

    payment_channel: Optional[str] = FieldInfo(alias="paymentChannel", default=None)

    type: Optional[str] = None


class TransactionRetrievePendingResponse(BaseModel):
    data: List[Data]

    limit: int

    offset: int

    total: int

    next_offset: Optional[int] = FieldInfo(alias="nextOffset", default=None)
