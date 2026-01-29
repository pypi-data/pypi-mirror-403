# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["AnomalyListParams"]


class AnomalyListParams(TypedDict, total=False):
    end_date: Annotated[str, PropertyInfo(alias="endDate")]
    """End date for filtering results (inclusive, YYYY-MM-DD)."""

    entity_type: Annotated[str, PropertyInfo(alias="entityType")]
    """Filter anomalies by the type of financial entity they are related to."""

    limit: int
    """Maximum number of items to return in a single page."""

    offset: int
    """Number of items to skip before starting to collect the result set."""

    severity: str
    """Filter anomalies by their AI-assessed severity level."""

    start_date: Annotated[str, PropertyInfo(alias="startDate")]
    """Start date for filtering results (inclusive, YYYY-MM-DD)."""

    status: str
    """Filter anomalies by their current review status."""
