"""The normalized tunnel type ID. enumeration."""

from enum import IntEnum


class TunnelTypeId(IntEnum):
    """The normalized tunnel type ID.

    See: https://schema.ocsf.io/1.6.0/data_types/tunnel_type_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_99 = 99  #
