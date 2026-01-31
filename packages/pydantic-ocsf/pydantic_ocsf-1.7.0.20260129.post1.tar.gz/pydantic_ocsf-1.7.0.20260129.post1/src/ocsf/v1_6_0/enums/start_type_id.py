"""The start type ID of the startup item. enumeration."""

from enum import IntEnum


class StartTypeId(IntEnum):
    """The start type ID of the startup item.

    See: https://schema.ocsf.io/1.6.0/data_types/start_type_id
    """

    VALUE_0 = 0  # The start type is unknown.
    VALUE_1 = 1  # Service started automatically during system startup.
    VALUE_2 = 2  # Device driver started by the system loader.
    VALUE_3 = 3  # Started on demand. For example, by the Windows Service Control Manager when a process calls the <i>StartService</i> function.
    VALUE_4 = 4  # The service is disabled, and cannot be started.
    VALUE_5 = 5  # Started on all user logins.
    VALUE_6 = 6  # Started on specific user logins.
    VALUE_7 = 7  # Stared according to a schedule.
    VALUE_8 = 8  # Started when a system item, such as a file or registry key, changes.
    VALUE_99 = 99  # The start type is not mapped. See the <code>start_type</code> attribute, which contains a data source specific value.
