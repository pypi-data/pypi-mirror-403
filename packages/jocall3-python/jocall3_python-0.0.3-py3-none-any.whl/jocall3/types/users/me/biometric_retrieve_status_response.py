# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["BiometricRetrieveStatusResponse", "EnrolledBiometric"]


class EnrolledBiometric(BaseModel):
    device_id: Optional[str] = FieldInfo(alias="deviceId", default=None)

    enrollment_date: Optional[datetime] = FieldInfo(alias="enrollmentDate", default=None)

    type: Optional[str] = None


class BiometricRetrieveStatusResponse(BaseModel):
    """Current biometric enrollment status for a user."""

    biometrics_enrolled: bool = FieldInfo(alias="biometricsEnrolled")

    enrolled_biometrics: List[EnrolledBiometric] = FieldInfo(alias="enrolledBiometrics")

    last_used: Optional[datetime] = FieldInfo(alias="lastUsed", default=None)
