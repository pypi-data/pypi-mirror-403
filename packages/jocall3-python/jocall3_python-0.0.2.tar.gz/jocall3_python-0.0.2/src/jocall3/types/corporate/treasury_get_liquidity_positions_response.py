# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["TreasuryGetLiquidityPositionsResponse"]


class TreasuryGetLiquidityPositionsResponse(BaseModel):
    ai_liquidity_assessment: object = FieldInfo(alias="aiLiquidityAssessment")
    """AI's overall assessment of liquidity."""

    short_term_investments: object = FieldInfo(alias="shortTermInvestments")
    """Details on short-term investments contributing to liquidity."""
