# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["BudgetListResponse", "Data", "DataCategory"]


class DataCategory(BaseModel):
    allocated: Optional[float] = None

    name: Optional[str] = None

    remaining: Optional[float] = None

    spent: Optional[float] = None


class Data(BaseModel):
    id: Optional[str] = None

    alert_threshold: Optional[int] = FieldInfo(alias="alertThreshold", default=None)

    categories: Optional[List[DataCategory]] = None

    end_date: Optional[date] = FieldInfo(alias="endDate", default=None)

    name: Optional[str] = None

    period: Optional[str] = None

    remaining_amount: Optional[float] = FieldInfo(alias="remainingAmount", default=None)

    spent_amount: Optional[float] = FieldInfo(alias="spentAmount", default=None)

    start_date: Optional[date] = FieldInfo(alias="startDate", default=None)

    status: Optional[str] = None

    total_amount: Optional[float] = FieldInfo(alias="totalAmount", default=None)


class BudgetListResponse(BaseModel):
    data: List[Data]

    limit: int

    offset: int

    total: int

    next_offset: Optional[int] = FieldInfo(alias="nextOffset", default=None)
