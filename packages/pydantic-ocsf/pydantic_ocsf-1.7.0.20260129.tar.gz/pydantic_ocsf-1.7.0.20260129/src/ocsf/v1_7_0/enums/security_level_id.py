"""The current security level of the entity enumeration."""

from enum import IntEnum


class SecurityLevelId(IntEnum):
    """The current security level of the entity

    See: https://schema.ocsf.io/1.7.0/data_types/security_level_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_99 = 99  # The security level is not mapped. See the <code>security_level</code> attribute, which contains data source specific values.
