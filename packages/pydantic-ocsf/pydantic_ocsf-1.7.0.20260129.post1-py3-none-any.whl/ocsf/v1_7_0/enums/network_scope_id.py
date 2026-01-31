"""The normalized identifier of the endpoint’s network scope. The normalized network scope identifier indicates whether the endpoint resides inside the customer’s network, outside on the Internet, or if its location relative to the customer’s network cannot be determined. enumeration."""

from enum import IntEnum


class NetworkScopeId(IntEnum):
    """The normalized identifier of the endpoint’s network scope. The normalized network scope identifier indicates whether the endpoint resides inside the customer’s network, outside on the Internet, or if its location relative to the customer’s network cannot be determined.

    See: https://schema.ocsf.io/1.7.0/data_types/network_scope_id
    """

    VALUE_0 = 0  # Unknown whether this endpoint resides within the customer’s network.
    VALUE_1 = 1  # The endpoint resides inside the customer’s network.
    VALUE_2 = 2  # The endpoint is on the Internet or otherwise external to the customer’s network.
    VALUE_99 = 99  # The network scope is not mapped. See the <code>network_scope</code> attribute, which contains a data source specific value.
