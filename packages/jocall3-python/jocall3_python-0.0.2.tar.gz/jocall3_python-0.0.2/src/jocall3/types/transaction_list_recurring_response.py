# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TransactionListRecurringResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None

    ai_confidence_score: Optional[float] = FieldInfo(alias="aiConfidenceScore", default=None)

    amount: Optional[float] = None

    category: Optional[str] = None

    currency: Optional[str] = None

    description: Optional[str] = None

    frequency: Optional[str] = None

    last_paid_date: Optional[date] = FieldInfo(alias="lastPaidDate", default=None)

    linked_account_id: Optional[str] = FieldInfo(alias="linkedAccountId", default=None)

    next_due_date: Optional[date] = FieldInfo(alias="nextDueDate", default=None)

    status: Optional[str] = None


class TransactionListRecurringResponse(BaseModel):
    data: List[Data]

    limit: int

    offset: int

    total: int

    next_offset: Optional[int] = FieldInfo(alias="nextOffset", default=None)
