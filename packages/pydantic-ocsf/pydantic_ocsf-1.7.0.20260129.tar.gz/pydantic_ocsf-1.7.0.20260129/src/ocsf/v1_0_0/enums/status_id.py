"""The normalized identifier of the event status. enumeration."""

from enum import IntEnum


class StatusId(IntEnum):
    """The normalized identifier of the event status.

    See: https://schema.ocsf.io/1.0.0/data_types/status_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_99 = 99  # The event status is not mapped. See the <code>status</code> attribute, which contains a data source specific value.
