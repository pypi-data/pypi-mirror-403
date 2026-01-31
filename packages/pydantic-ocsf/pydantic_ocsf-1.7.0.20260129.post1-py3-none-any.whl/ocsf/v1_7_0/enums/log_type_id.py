"""The normalized log type identifier. enumeration."""

from enum import IntEnum


class LogTypeId(IntEnum):
    """The normalized log type identifier.

    See: https://schema.ocsf.io/1.7.0/data_types/log_type_id
    """

    VALUE_0 = 0  # The log type is unknown.
    VALUE_1 = 1  # The log type is an Operating System log.
    VALUE_2 = 2  # The log type is an Application log.
    VALUE_99 = 99  # The log type is not mapped. See the <code>log_type</code> attribute, which contains a data source specific value.
