# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["CashFlowForecastResponse"]


class CashFlowForecastResponse(BaseModel):
    inflow_forecast: object = FieldInfo(alias="inflowForecast")
    """Forecast of cash inflows by source."""

    outflow_forecast: object = FieldInfo(alias="outflowForecast")
    """Forecast of cash outflows by category."""
