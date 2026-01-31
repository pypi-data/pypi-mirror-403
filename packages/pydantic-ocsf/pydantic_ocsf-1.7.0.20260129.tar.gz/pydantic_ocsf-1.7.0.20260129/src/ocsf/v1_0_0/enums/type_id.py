"""The normalized account type identifier. enumeration."""

from enum import IntEnum


class TypeId(IntEnum):
    """The normalized account type identifier.

    See: https://schema.ocsf.io/1.0.0/data_types/type_id
    """

    VALUE_0 = 0  # The account type is unknown.
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_4 = 4  #
    VALUE_5 = 5  #
    VALUE_6 = 6  #
    VALUE_7 = 7  #
    VALUE_8 = 8  #
    VALUE_9 = 9  #
    VALUE_10 = 10  #
    VALUE_99 = 99  # The account type is not mapped.
