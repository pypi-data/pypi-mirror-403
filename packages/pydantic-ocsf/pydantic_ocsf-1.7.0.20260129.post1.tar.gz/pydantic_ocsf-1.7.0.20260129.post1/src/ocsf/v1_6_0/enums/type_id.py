"""The normalized account type identifier. enumeration."""

from enum import IntEnum


class TypeId(IntEnum):
    """The normalized account type identifier.

    See: https://schema.ocsf.io/1.6.0/data_types/type_id
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
    VALUE_11 = 11  #
    VALUE_12 = 12  #
    VALUE_13 = 13  #
    VALUE_14 = 14  #
    VALUE_15 = 15  #
    VALUE_16 = 16  #
    VALUE_17 = 17  #
    VALUE_18 = 18  #
    VALUE_99 = 99  # The account type is not mapped.
