"""The state of the TCP socket for the network connection. enumeration."""

from enum import IntEnum


class TcpStateId(IntEnum):
    """The state of the TCP socket for the network connection.

    See: https://schema.ocsf.io/1.6.0/data_types/tcp_state_id
    """

    VALUE_0 = 0  # The socket state is unknown.
    VALUE_1 = (
        1  # The socket has an established connection between a local application and a remote peer.
    )
    VALUE_2 = 2  # The socket is actively trying to establish a connection to a remote peer.
    VALUE_3 = 3  # The socket has passively received a connection request from a remote peer.
    VALUE_4 = 4  # The socket connection has been closed by the local application, the remote peer has not yet acknowledged the close, and the system is waiting for it to close its half of the connection.
    VALUE_5 = 5  # The socket connection has been closed by the local application, the remote peer has acknowledged the close, and the system is waiting for it to close its half of the connection.
    VALUE_6 = 6  # The socket connection has been closed by the local application, the remote peer has closed its half of the connection, and the system is waiting to be sure that the remote peer received the last acknowledgement.
    VALUE_7 = 7  # The socket is not in use.
    VALUE_8 = 8  # The socket connection has been closed by the remote peer, and the system is waiting for the local application to close its half of the connection.
    VALUE_9 = 9  # The socket connection has been closed by the remote peer, the local application has closed its half of the connection, and the system is waiting for the remote peer to acknowledge the close.
    VALUE_10 = 10  # The socket is listening for incoming connections.
    VALUE_11 = 11  # The socket connection has been closed by the local application and the remote peer simultaneously, and the remote peer has not yet acknowledged the close attempt of the local application.
