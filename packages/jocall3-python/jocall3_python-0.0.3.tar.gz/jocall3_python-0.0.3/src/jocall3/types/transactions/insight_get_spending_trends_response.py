# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["InsightGetSpendingTrendsResponse", "AIInsight", "TopCategoriesByChange"]


class AIInsight(BaseModel):
    id: Optional[str] = None

    actionable_recommendation: Optional[str] = FieldInfo(alias="actionableRecommendation", default=None)

    category: Optional[str] = None

    description: Optional[str] = None

    severity: Optional[str] = None

    timestamp: Optional[datetime] = None

    title: Optional[str] = None


class TopCategoriesByChange(BaseModel):
    absolute_change: Optional[float] = FieldInfo(alias="absoluteChange", default=None)

    category: Optional[str] = None

    percentage_change: Optional[float] = FieldInfo(alias="percentageChange", default=None)


class InsightGetSpendingTrendsResponse(BaseModel):
    ai_insights: List[AIInsight] = FieldInfo(alias="aiInsights")

    forecast_next_month: float = FieldInfo(alias="forecastNextMonth")

    overall_trend: str = FieldInfo(alias="overallTrend")

    percentage_change: float = FieldInfo(alias="percentageChange")

    period: str

    top_categories_by_change: List[TopCategoriesByChange] = FieldInfo(alias="topCategoriesByChange")
