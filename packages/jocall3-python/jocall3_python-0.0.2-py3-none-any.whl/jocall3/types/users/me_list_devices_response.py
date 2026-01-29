# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["MeListDevicesResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None

    ip_address: Optional[str] = FieldInfo(alias="ipAddress", default=None)

    last_active: Optional[datetime] = FieldInfo(alias="lastActive", default=None)

    model: Optional[str] = None

    os: Optional[str] = None

    push_token: Optional[str] = FieldInfo(alias="pushToken", default=None)

    trust_level: Optional[str] = FieldInfo(alias="trustLevel", default=None)

    type: Optional[str] = None


class MeListDevicesResponse(BaseModel):
    data: List[Data]

    limit: int

    offset: int

    total: int

    next_offset: Optional[int] = FieldInfo(alias="nextOffset", default=None)
