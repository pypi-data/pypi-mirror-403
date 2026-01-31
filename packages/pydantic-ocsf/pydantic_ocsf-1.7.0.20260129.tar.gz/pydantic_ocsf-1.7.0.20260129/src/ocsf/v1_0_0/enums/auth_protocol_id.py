"""The normalized identifier of the authentication protocol used to create the user session. enumeration."""

from enum import IntEnum


class AuthProtocolId(IntEnum):
    """The normalized identifier of the authentication protocol used to create the user session.

    See: https://schema.ocsf.io/1.0.0/data_types/auth_protocol_id
    """

    VALUE_0 = 0  #
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
    VALUE_99 = 99  #
