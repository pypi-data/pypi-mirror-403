# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime
from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TransactionListResponse", "Data", "DataLocation", "DataMerchantDetails", "DataMerchantDetailsAddress"]


class DataLocation(BaseModel):
    city: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None


class DataMerchantDetailsAddress(BaseModel):
    city: Optional[str] = None

    state: Optional[str] = None

    zip: Optional[str] = None


class DataMerchantDetails(BaseModel):
    address: Optional[DataMerchantDetailsAddress] = None

    logo_url: Optional[str] = FieldInfo(alias="logoUrl", default=None)

    name: Optional[str] = None

    website: Optional[str] = None


class Data(BaseModel):
    id: Optional[str] = None

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)

    ai_category_confidence: Optional[float] = FieldInfo(alias="aiCategoryConfidence", default=None)

    amount: Optional[float] = None

    carbon_footprint: Optional[float] = FieldInfo(alias="carbonFootprint", default=None)

    category: Optional[str] = None

    currency: Optional[str] = None

    date: Optional[datetime.date] = None

    description: Optional[str] = None

    dispute_status: Optional[str] = FieldInfo(alias="disputeStatus", default=None)

    location: Optional[DataLocation] = None

    merchant_details: Optional[DataMerchantDetails] = FieldInfo(alias="merchantDetails", default=None)

    notes: Optional[str] = None

    payment_channel: Optional[str] = FieldInfo(alias="paymentChannel", default=None)

    posted_date: Optional[datetime.date] = FieldInfo(alias="postedDate", default=None)

    receipt_url: Optional[str] = FieldInfo(alias="receiptUrl", default=None)

    tags: Optional[List[str]] = None

    type: Optional[str] = None


class TransactionListResponse(BaseModel):
    data: List[Data]

    limit: int

    offset: int

    total: int

    next_offset: Optional[int] = FieldInfo(alias="nextOffset", default=None)
