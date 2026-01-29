# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["MeUpdateParams", "Address", "Preferences", "PreferencesNotificationChannels"]


class MeUpdateParams(TypedDict, total=False):
    address: Address

    name: str

    phone: str

    preferences: Preferences
    """User's personalized preferences for the platform."""


class Address(TypedDict, total=False):
    city: str

    country: str

    state: str

    street: str

    zip: str


class PreferencesNotificationChannels(TypedDict, total=False):
    """Preferred channels for receiving notifications."""

    email: bool

    in_app: Annotated[bool, PropertyInfo(alias="inApp")]

    push: bool

    sms: bool


class Preferences(TypedDict, total=False):
    """User's personalized preferences for the platform."""

    ai_interaction_mode: Annotated[str, PropertyInfo(alias="aiInteractionMode")]

    data_sharing_consent: Annotated[bool, PropertyInfo(alias="dataSharingConsent")]

    notification_channels: Annotated[PreferencesNotificationChannels, PropertyInfo(alias="notificationChannels")]
    """Preferred channels for receiving notifications."""

    preferred_language: Annotated[str, PropertyInfo(alias="preferredLanguage")]

    theme: str

    transaction_grouping: Annotated[str, PropertyInfo(alias="transactionGrouping")]
