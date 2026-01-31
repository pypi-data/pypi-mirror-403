"""The normalized identifier of the SSH authentication type. enumeration."""

from enum import IntEnum


class AuthTypeId(IntEnum):
    """The normalized identifier of the SSH authentication type.

    See: https://schema.ocsf.io/1.2.0/data_types/auth_type_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  # Authentication using digital certificates.
    VALUE_2 = 2  # GSSAPI for centralized authentication.
    VALUE_3 = 3  # Authentication based on the client host's identity.
    VALUE_4 = 4  # Multi-step, interactive authentication.
    VALUE_5 = 5  # Password Authentication.
    VALUE_6 = 6  # Paired public key authentication.
    VALUE_99 = 99  #
