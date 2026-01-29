# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["PreferenceUpdateParams", "NotificationChannels"]


class PreferenceUpdateParams(TypedDict, total=False):
    ai_interaction_mode: Annotated[str, PropertyInfo(alias="aiInteractionMode")]

    data_sharing_consent: Annotated[bool, PropertyInfo(alias="dataSharingConsent")]

    notification_channels: Annotated[NotificationChannels, PropertyInfo(alias="notificationChannels")]
    """Preferred channels for receiving notifications."""

    preferred_language: Annotated[str, PropertyInfo(alias="preferredLanguage")]

    theme: str

    transaction_grouping: Annotated[str, PropertyInfo(alias="transactionGrouping")]


class NotificationChannels(TypedDict, total=False):
    """Preferred channels for receiving notifications."""

    email: bool

    in_app: Annotated[bool, PropertyInfo(alias="inApp")]

    push: bool

    sms: bool
