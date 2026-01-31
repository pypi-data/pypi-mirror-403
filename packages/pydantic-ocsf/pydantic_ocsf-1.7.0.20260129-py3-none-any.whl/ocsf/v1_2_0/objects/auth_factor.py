"""Authentication Factor object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.enums.factor_type_id import FactorTypeId
    from ocsf.v1_2_0.objects.device import Device


class AuthFactor(OCSFBaseModel):
    """An Authentication Factor object describes a category of methods used for identity verification in an authentication attempt.

    See: https://schema.ocsf.io/1.2.0/objects/auth_factor
    """

    factor_type_id: FactorTypeId = Field(
        ..., description="The normalized identifier for the authentication factor."
    )
    device: Device | None = Field(
        default=None, description="Device used to complete an authentication request. [Recommended]"
    )
    email_addr: Any | None = Field(
        default=None, description="The email address used in an email-based authentication factor."
    )
    factor_type: str | None = Field(
        default=None,
        description="The type of authentication factor used in an authentication attempt. [Recommended]",
    )
    is_hotp: bool | None = Field(
        default=None,
        description="Whether the authentication factor is an HMAC-based One-time Password (HOTP). [Recommended]",
    )
    is_totp: bool | None = Field(
        default=None,
        description="Whether the authentication factor is a Time-based One-time Password (TOTP). [Recommended]",
    )
    phone_number: str | None = Field(
        default=None,
        description="The phone number used for a telephony-based authentication request.",
    )
    provider: str | None = Field(
        default=None, description="The name of provider for an authentication factor. [Recommended]"
    )
    security_questions: list[str] | None = Field(
        default=None,
        description="The question(s) provided to user for a question-based authentication factor.",
    )
