"""The Internet Protocol version identifier. enumeration."""

from enum import IntEnum


class ProtocolVerId(IntEnum):
    """The Internet Protocol version identifier.

    See: https://schema.ocsf.io/1.5.0/data_types/protocol_ver_id
    """

    VALUE_0 = 0  #
    VALUE_4 = 4  #
    VALUE_6 = 6  #
    VALUE_99 = 99  #
