"""The normalized state identifier of a security finding. enumeration."""

from enum import IntEnum


class StateId(IntEnum):
    """The normalized state identifier of a security finding.

    See: https://schema.ocsf.io/1.0.0/data_types/state_id
    """

    VALUE_1 = 1  # The finding is new and yet to be reviewed.
    VALUE_2 = 2  # The finding is under review.
    VALUE_3 = 3  # The finding was reviewed, considered as a false positive and is now suppressed.
    VALUE_4 = 4  # The finding was reviewed and remediated and is now considered resolved.
