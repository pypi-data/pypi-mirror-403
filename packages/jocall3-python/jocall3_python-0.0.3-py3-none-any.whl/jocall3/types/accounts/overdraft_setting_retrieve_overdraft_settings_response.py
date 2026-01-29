# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["OverdraftSettingRetrieveOverdraftSettingsResponse"]


class OverdraftSettingRetrieveOverdraftSettingsResponse(BaseModel):
    account_id: str = FieldInfo(alias="accountId")

    enabled: bool

    fee_preference: str = FieldInfo(alias="feePreference")

    linked_savings_account_id: Optional[str] = FieldInfo(alias="linkedSavingsAccountId", default=None)

    link_to_savings: Optional[bool] = FieldInfo(alias="linkToSavings", default=None)

    protection_limit: Optional[float] = FieldInfo(alias="protectionLimit", default=None)
