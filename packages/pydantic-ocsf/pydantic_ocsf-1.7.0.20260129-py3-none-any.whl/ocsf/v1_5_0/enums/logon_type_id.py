"""The normalized logon type identifier. enumeration."""

from enum import IntEnum


class LogonTypeId(IntEnum):
    """The normalized logon type identifier.

    See: https://schema.ocsf.io/1.5.0/data_types/logon_type_id
    """

    VALUE_0 = 0  # The logon type is unknown.
    VALUE_1 = 1  # Used only by the System account, for example at system startup.
    VALUE_2 = 2  # A local logon to device console.
    VALUE_3 = 3  # A user or device logged onto this device from the network.
    VALUE_4 = 4  # A batch server logon, where processes may be executing on behalf of a user without their direct intervention.
    VALUE_5 = 5  # A logon by a service or daemon that was started by the OS.
    VALUE_7 = 7  # A user unlocked the device.
    VALUE_8 = 8  # A user logged on to this device from the network. The user's password in the authentication package was not hashed.
    VALUE_9 = 9  # A caller cloned its current token and specified new credentials for outbound connections. The new logon session has the same local identity, but uses different credentials for other network connections.
    VALUE_10 = 10  # A remote logon using Terminal Services or remote desktop application.
    VALUE_11 = 11  # A user logged on to this device with network credentials that were stored locally on the device and the domain controller was not contacted to verify the credentials.
    VALUE_12 = 12  # Same as Remote Interactive. This is used for internal auditing.
    VALUE_13 = 13  # Workstation logon.
    VALUE_99 = 99  # The logon type is not mapped. See the <code>logon_type</code> attribute, which contains a data source specific value.
