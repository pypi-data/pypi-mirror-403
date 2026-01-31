"""The normalized install state ID of the Advisory. enumeration."""

from enum import IntEnum


class InstallStateId(IntEnum):
    """The normalized install state ID of the Advisory.

    See: https://schema.ocsf.io/1.7.0/data_types/install_state_id
    """

    VALUE_0 = 0  # The normalized install state is unknown.
    VALUE_1 = 1  # The item is installed.
    VALUE_2 = 2  # The item is not installed.
    VALUE_3 = 3  # The item is installed pending reboot operation.
    VALUE_99 = 99  # The install state is not mapped. See the <code>install_state</code> attribute, which contains a data source specific value.
