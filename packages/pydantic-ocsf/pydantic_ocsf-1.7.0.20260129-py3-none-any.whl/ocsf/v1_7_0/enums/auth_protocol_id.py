"""The normalized identifier of the authorization protocol used by the SCIM resource. enumeration."""

from enum import IntEnum


class AuthProtocolId(IntEnum):
    """The normalized identifier of the authorization protocol used by the SCIM resource.

    See: https://schema.ocsf.io/1.7.0/data_types/auth_protocol_id
    """

    VALUE_0 = 0  # The authentication protocol is unknown.
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
    VALUE_99 = 99  # The authentication protocol is not mapped. See the <code>auth_protocol</code> attribute, which contains a data source specific value.
