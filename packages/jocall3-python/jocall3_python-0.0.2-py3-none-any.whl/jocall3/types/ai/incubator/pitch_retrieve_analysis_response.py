# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["PitchRetrieveAnalysisResponse", "AIFinancialModel"]


class AIFinancialModel(BaseModel):
    """AI's detailed financial model analysis."""

    cost_structure_analysis: Optional[object] = FieldInfo(alias="costStructureAnalysis", default=None)

    revenue_breakdown: Optional[object] = FieldInfo(alias="revenueBreakdown", default=None)


class PitchRetrieveAnalysisResponse(BaseModel):
    ai_coaching_plan: Optional[object] = FieldInfo(alias="aiCoachingPlan", default=None)
    """AI-generated coaching plan for the entrepreneur."""

    ai_financial_model: Optional[AIFinancialModel] = FieldInfo(alias="aiFinancialModel", default=None)
    """AI's detailed financial model analysis."""

    ai_market_analysis: Optional[object] = FieldInfo(alias="aiMarketAnalysis", default=None)
    """AI's detailed market analysis."""

    ai_risk_assessment: Optional[object] = FieldInfo(alias="aiRiskAssessment", default=None)
    """AI's assessment of risks associated with the venture."""
