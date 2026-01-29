# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["OverdraftSettingUpdateOverdraftSettingsParams"]


class OverdraftSettingUpdateOverdraftSettingsParams(TypedDict, total=False):
    enabled: bool

    fee_preference: Annotated[str, PropertyInfo(alias="feePreference")]

    link_to_savings: Annotated[bool, PropertyInfo(alias="linkToSavings")]
