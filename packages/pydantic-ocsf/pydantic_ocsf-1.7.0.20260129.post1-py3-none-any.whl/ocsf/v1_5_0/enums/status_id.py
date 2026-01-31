"""The normalized status identifier of the compliance check. enumeration."""

from enum import IntEnum


class StatusId(IntEnum):
    """The normalized status identifier of the compliance check.

    See: https://schema.ocsf.io/1.5.0/data_types/status_id
    """

    VALUE_0 = 0  # The status is unknown.
    VALUE_1 = 1  # The compliance check passed for all the evaluated resources.
    VALUE_2 = 2  # The compliance check did not yield a result due to missing information.
    VALUE_3 = 3  # The compliance check failed for at least one of the evaluated resources.
    VALUE_99 = 99  # The event status is not mapped. See the <code>status</code> attribute, which contains a data source specific value.
