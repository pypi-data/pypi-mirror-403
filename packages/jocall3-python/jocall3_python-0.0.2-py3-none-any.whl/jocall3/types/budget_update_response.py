# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["BudgetUpdateResponse", "Category"]


class Category(BaseModel):
    allocated: Optional[float] = None

    name: Optional[str] = None

    remaining: Optional[float] = None

    spent: Optional[float] = None


class BudgetUpdateResponse(BaseModel):
    id: str

    alert_threshold: int = FieldInfo(alias="alertThreshold")

    categories: List[Category]

    end_date: date = FieldInfo(alias="endDate")

    name: str

    period: str

    remaining_amount: float = FieldInfo(alias="remainingAmount")

    spent_amount: float = FieldInfo(alias="spentAmount")

    start_date: date = FieldInfo(alias="startDate")

    status: str

    total_amount: float = FieldInfo(alias="totalAmount")
