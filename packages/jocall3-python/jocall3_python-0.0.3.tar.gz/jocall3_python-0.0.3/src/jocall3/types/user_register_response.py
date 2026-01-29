# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import date, datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["UserRegisterResponse", "Address", "Preferences", "PreferencesNotificationChannels", "SecurityStatus"]


class Address(BaseModel):
    city: Optional[str] = None

    country: Optional[str] = None

    state: Optional[str] = None

    street: Optional[str] = None

    zip: Optional[str] = None


class PreferencesNotificationChannels(BaseModel):
    """Preferred channels for receiving notifications."""

    email: Optional[bool] = None

    in_app: Optional[bool] = FieldInfo(alias="inApp", default=None)

    push: Optional[bool] = None

    sms: Optional[bool] = None


class Preferences(BaseModel):
    """User's personalized preferences for the platform."""

    ai_interaction_mode: Optional[str] = FieldInfo(alias="aiInteractionMode", default=None)

    data_sharing_consent: Optional[bool] = FieldInfo(alias="dataSharingConsent", default=None)

    notification_channels: Optional[PreferencesNotificationChannels] = FieldInfo(
        alias="notificationChannels", default=None
    )
    """Preferred channels for receiving notifications."""

    preferred_language: Optional[str] = FieldInfo(alias="preferredLanguage", default=None)

    theme: Optional[str] = None

    transaction_grouping: Optional[str] = FieldInfo(alias="transactionGrouping", default=None)


class SecurityStatus(BaseModel):
    """Security-related status for the user account."""

    biometrics_enrolled: Optional[bool] = FieldInfo(alias="biometricsEnrolled", default=None)

    last_login: Optional[datetime] = FieldInfo(alias="lastLogin", default=None)

    last_login_ip: Optional[str] = FieldInfo(alias="lastLoginIp", default=None)

    two_factor_enabled: Optional[bool] = FieldInfo(alias="twoFactorEnabled", default=None)


class UserRegisterResponse(BaseModel):
    id: str

    email: str

    identity_verified: bool = FieldInfo(alias="identityVerified")

    name: str

    address: Optional[Address] = None

    ai_persona: Optional[str] = FieldInfo(alias="aiPersona", default=None)

    date_of_birth: Optional[date] = FieldInfo(alias="dateOfBirth", default=None)

    gamification_level: Optional[int] = FieldInfo(alias="gamificationLevel", default=None)

    loyalty_points: Optional[int] = FieldInfo(alias="loyaltyPoints", default=None)

    loyalty_tier: Optional[str] = FieldInfo(alias="loyaltyTier", default=None)

    phone: Optional[str] = None

    preferences: Optional[Preferences] = None
    """User's personalized preferences for the platform."""

    security_status: Optional[SecurityStatus] = FieldInfo(alias="securityStatus", default=None)
    """Security-related status for the user account."""
