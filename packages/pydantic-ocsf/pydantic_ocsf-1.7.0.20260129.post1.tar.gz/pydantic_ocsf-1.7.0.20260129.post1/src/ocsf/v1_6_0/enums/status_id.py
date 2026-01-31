"""The normalized status identifier indicating the applicability of this policy restriction. enumeration."""

from enum import IntEnum


class StatusId(IntEnum):
    """The normalized status identifier indicating the applicability of this policy restriction.

    See: https://schema.ocsf.io/1.6.0/data_types/status_id
    """

    VALUE_1 = 1  # This restriction is currently applicable and being enforced.
    VALUE_2 = 2  # This restriction is not applicable.
    VALUE_3 = 3  # This restriction could not be properly evaluated due to an error.
