"""The list of DNS answer header flag IDs. enumeration."""

from enum import IntEnum


class FlagIds(IntEnum):
    """The list of DNS answer header flag IDs.

    See: https://schema.ocsf.io/1.1.0/data_types/flag_ids
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_4 = 4  #
    VALUE_5 = 5  #
    VALUE_6 = 6  #
    VALUE_99 = 99  # The event DNS header flag is not mapped.
