"""The security state of the managed entity. enumeration."""

from enum import IntEnum


class StateId(IntEnum):
    """The security state of the managed entity.

    See: https://schema.ocsf.io/1.1.0/data_types/state_id
    """

    VALUE_0 = 0  # The security state is unknown.
    VALUE_1 = 1  # The content is missing or outdated.
    VALUE_2 = 2  # Not in compliance with the expected security policy.
    VALUE_3 = 3  # Isolated from the network.
    VALUE_4 = 4  # Not protected by a security solution.
    VALUE_5 = 5  # The security solution is not functioning properly.
    VALUE_6 = 6  # The security solution does not have a valid license.
    VALUE_7 = 7  # A detected threat has not been remediated.
    VALUE_8 = 8  # Reputation of the entity is suspicious.
    VALUE_9 = 9  # A reboot is required for one or more pending actions.
    VALUE_10 = 10  # The content is locked to a specific version.
    VALUE_11 = 11  # The entity is not installed.
    VALUE_12 = 12  # The system partition is writeable.
    VALUE_13 = 13  # The device has failed the SafetyNet check.
    VALUE_14 = 14  # The device has failed the boot verification process.
    VALUE_15 = 15  # The execution environment has been modified.
    VALUE_16 = 16  # The SELinux security feature has been disabled.
    VALUE_17 = 17  # An elevated privilege shell has been detected.
    VALUE_18 = 18  # The file system has been altered on an iOS device.
    VALUE_19 = 19  # Remote access is enabled.
    VALUE_20 = 20  # Mobile OTA (Over The Air) updates have been disabled.
    VALUE_21 = 21  # The device has been modified to allow root access.
    VALUE_22 = 22  # The Android partition has been modified.
    VALUE_23 = 23  # The entity is not compliant with the associated security policy.
    VALUE_99 = 99  # The security state is not mapped. See the <code>state</code> attribute, which contains data source specific values.
