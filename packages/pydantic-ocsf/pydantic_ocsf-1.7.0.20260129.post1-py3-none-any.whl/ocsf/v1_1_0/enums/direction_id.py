"""The normalized identifier of the direction of the initiated connection, traffic, or email. enumeration."""

from enum import IntEnum


class DirectionId(IntEnum):
    """The normalized identifier of the direction of the initiated connection, traffic, or email.

    See: https://schema.ocsf.io/1.1.0/data_types/direction_id
    """

    VALUE_0 = 0  # The connection direction is unknown.
    VALUE_1 = 1  # Inbound network connection. The connection was originated from the Internet or outside network, destined for services on the inside network.
    VALUE_2 = 2  # Outbound network connection. The connection was originated from inside the network, destined for services on the Internet or outside network.
    VALUE_3 = 3  # Lateral network connection. The connection was originated from inside the network, destined for services on the inside network.
    VALUE_99 = 99  # The direction is not mapped. See the <code>direction</code> attribute, which contains a data source specific value.
