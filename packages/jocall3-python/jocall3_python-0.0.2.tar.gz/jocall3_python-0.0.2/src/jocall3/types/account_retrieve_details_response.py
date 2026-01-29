# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime
from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["AccountRetrieveDetailsResponse", "BalanceHistory", "ProjectedCashFlow"]


class BalanceHistory(BaseModel):
    balance: Optional[float] = None

    date: Optional[datetime.date] = None


class ProjectedCashFlow(BaseModel):
    confidence_score: Optional[int] = FieldInfo(alias="confidenceScore", default=None)

    days30: Optional[float] = None

    days90: Optional[float] = None


class AccountRetrieveDetailsResponse(BaseModel):
    id: str

    currency: str

    current_balance: float = FieldInfo(alias="currentBalance")

    institution_name: str = FieldInfo(alias="institutionName")

    last_updated: datetime.datetime = FieldInfo(alias="lastUpdated")

    name: str

    type: str

    account_holder: Optional[str] = FieldInfo(alias="accountHolder", default=None)

    available_balance: Optional[float] = FieldInfo(alias="availableBalance", default=None)

    balance_history: Optional[List[BalanceHistory]] = FieldInfo(alias="balanceHistory", default=None)

    external_id: Optional[str] = FieldInfo(alias="externalId", default=None)

    interest_rate: Optional[float] = FieldInfo(alias="interestRate", default=None)

    mask: Optional[str] = None

    opened_date: Optional[datetime.date] = FieldInfo(alias="openedDate", default=None)

    projected_cash_flow: Optional[ProjectedCashFlow] = FieldInfo(alias="projectedCashFlow", default=None)

    subtype: Optional[str] = None

    transactions_count: Optional[int] = FieldInfo(alias="transactionsCount", default=None)
