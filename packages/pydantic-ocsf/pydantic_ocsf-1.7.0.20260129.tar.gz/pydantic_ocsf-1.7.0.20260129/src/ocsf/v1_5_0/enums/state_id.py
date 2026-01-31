"""The normalized identifier of the signature state. enumeration."""

from enum import IntEnum


class StateId(IntEnum):
    """The normalized identifier of the signature state.

    See: https://schema.ocsf.io/1.5.0/data_types/state_id
    """

    VALUE_1 = 1  # The digital signature is valid.
    VALUE_2 = 2  # The digital signature is not valid due to expiration of certificate.
    VALUE_3 = 3  # The digital signature is invalid due to certificate revocation.
    VALUE_4 = 4  # The digital signature is invalid due to certificate suspension.
    VALUE_5 = 5  # The digital signature state is pending.
