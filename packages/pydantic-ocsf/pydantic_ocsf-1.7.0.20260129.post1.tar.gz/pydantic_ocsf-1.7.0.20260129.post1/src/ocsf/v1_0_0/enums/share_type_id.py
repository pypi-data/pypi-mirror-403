"""The normalized identifier of the SMB share type. enumeration."""

from enum import IntEnum


class ShareTypeId(IntEnum):
    """The normalized identifier of the SMB share type.

    See: https://schema.ocsf.io/1.0.0/data_types/share_type_id
    """

    VALUE_0 = 0  # The share type is not known.
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_99 = 99  # The share type is not mapped.
