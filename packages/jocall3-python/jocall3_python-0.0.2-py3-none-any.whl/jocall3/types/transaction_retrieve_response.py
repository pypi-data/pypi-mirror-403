# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime
from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TransactionRetrieveResponse", "Location", "MerchantDetails", "MerchantDetailsAddress"]


class Location(BaseModel):
    city: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None


class MerchantDetailsAddress(BaseModel):
    city: Optional[str] = None

    state: Optional[str] = None

    zip: Optional[str] = None


class MerchantDetails(BaseModel):
    address: Optional[MerchantDetailsAddress] = None

    logo_url: Optional[str] = FieldInfo(alias="logoUrl", default=None)

    name: Optional[str] = None

    website: Optional[str] = None


class TransactionRetrieveResponse(BaseModel):
    id: str

    account_id: str = FieldInfo(alias="accountId")

    amount: float

    category: str

    currency: str

    date: datetime.date

    description: str

    type: str

    ai_category_confidence: Optional[float] = FieldInfo(alias="aiCategoryConfidence", default=None)

    carbon_footprint: Optional[float] = FieldInfo(alias="carbonFootprint", default=None)

    dispute_status: Optional[str] = FieldInfo(alias="disputeStatus", default=None)

    location: Optional[Location] = None

    merchant_details: Optional[MerchantDetails] = FieldInfo(alias="merchantDetails", default=None)

    notes: Optional[str] = None

    payment_channel: Optional[str] = FieldInfo(alias="paymentChannel", default=None)

    posted_date: Optional[datetime.date] = FieldInfo(alias="postedDate", default=None)

    receipt_url: Optional[str] = FieldInfo(alias="receiptUrl", default=None)

    tags: Optional[List[str]] = None
