"""The Analytic state identifier. enumeration."""

from enum import IntEnum


class StateId(IntEnum):
    """The Analytic state identifier.

    See: https://schema.ocsf.io/1.7.0/data_types/state_id
    """

    VALUE_1 = 1  # The Analytic is active.
    VALUE_2 = 2  # The Analytic is suppressed. For example, a user/customer has suppressed a particular detection signature in a security product.
    VALUE_3 = 3  # The Analytic is still under development and considered experimental.
