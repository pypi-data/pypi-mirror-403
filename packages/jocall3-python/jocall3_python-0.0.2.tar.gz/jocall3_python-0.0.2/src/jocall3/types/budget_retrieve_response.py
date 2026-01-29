# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date, datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["BudgetRetrieveResponse", "Category", "AIRecommendation"]


class Category(BaseModel):
    allocated: Optional[float] = None

    name: Optional[str] = None

    remaining: Optional[float] = None

    spent: Optional[float] = None


class AIRecommendation(BaseModel):
    id: Optional[str] = None

    actionable_recommendation: Optional[str] = FieldInfo(alias="actionableRecommendation", default=None)

    category: Optional[str] = None

    description: Optional[str] = None

    severity: Optional[str] = None

    timestamp: Optional[datetime] = None

    title: Optional[str] = None


class BudgetRetrieveResponse(BaseModel):
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

    ai_recommendations: Optional[List[AIRecommendation]] = FieldInfo(alias="aiRecommendations", default=None)
