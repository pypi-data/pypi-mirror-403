# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["AccountRetrieveMeResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None

    available_balance: Optional[float] = FieldInfo(alias="availableBalance", default=None)

    currency: Optional[str] = None

    current_balance: Optional[float] = FieldInfo(alias="currentBalance", default=None)

    external_id: Optional[str] = FieldInfo(alias="externalId", default=None)

    institution_name: Optional[str] = FieldInfo(alias="institutionName", default=None)

    last_updated: Optional[datetime] = FieldInfo(alias="lastUpdated", default=None)

    mask: Optional[str] = None

    name: Optional[str] = None

    subtype: Optional[str] = None

    type: Optional[str] = None


class AccountRetrieveMeResponse(BaseModel):
    data: List[Data]

    limit: int

    offset: int

    total: int

    next_offset: Optional[int] = FieldInfo(alias="nextOffset", default=None)
