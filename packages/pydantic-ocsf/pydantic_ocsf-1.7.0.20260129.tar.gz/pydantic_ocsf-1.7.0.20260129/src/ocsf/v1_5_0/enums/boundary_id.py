"""<p>The normalized identifier of the boundary of the connection. </p><p> For cloud connections, this translates to the traffic-boundary (same VPC, through IGW, etc.). For traditional networks, this is described as Local, Internal, or External.</p> enumeration."""

from enum import IntEnum


class BoundaryId(IntEnum):
    """<p>The normalized identifier of the boundary of the connection. </p><p> For cloud connections, this translates to the traffic-boundary (same VPC, through IGW, etc.). For traditional networks, this is described as Local, Internal, or External.</p>

    See: https://schema.ocsf.io/1.5.0/data_types/boundary_id
    """

    VALUE_0 = 0  # The connection boundary is unknown.
    VALUE_1 = 1  # Local network traffic on the same endpoint.
    VALUE_2 = 2  # Internal network traffic between two endpoints inside network.
    VALUE_3 = (
        3  # External network traffic between two endpoints on the Internet or outside the network.
    )
    VALUE_4 = 4  # Through another resource in the same VPC
    VALUE_5 = 5  # Through an Internet gateway or a gateway VPC endpoint
    VALUE_6 = 6  # Through a virtual private gateway
    VALUE_7 = 7  # Through an intra-region VPC peering connection
    VALUE_8 = 8  # Through an inter-region VPC peering connection
    VALUE_9 = 9  # Through a local gateway
    VALUE_10 = 10  # Through a gateway VPC endpoint (Nitro-based instances only)
    VALUE_11 = 11  # Through an Internet gateway (Nitro-based instances only)
    VALUE_99 = 99  # The boundary is not mapped. See the <code>boundary</code> attribute, which contains a data source specific value.
