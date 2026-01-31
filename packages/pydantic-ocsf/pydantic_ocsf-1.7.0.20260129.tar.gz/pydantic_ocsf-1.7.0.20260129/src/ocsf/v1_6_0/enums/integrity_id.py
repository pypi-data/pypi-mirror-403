"""The normalized identifier of the process integrity level (Windows only). enumeration."""

from enum import IntEnum


class IntegrityId(IntEnum):
    """The normalized identifier of the process integrity level (Windows only).

    See: https://schema.ocsf.io/1.6.0/data_types/integrity_id
    """

    VALUE_0 = 0  # The integrity level is unknown.
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_4 = 4  #
    VALUE_5 = 5  #
    VALUE_6 = 6  #
    VALUE_99 = 99  # The integrity level is not mapped. See the <code>integrity</code> attribute, which contains a data source specific value.
