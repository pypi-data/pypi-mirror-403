"""The previous security level of the entity enumeration."""

from enum import IntEnum


class PrevSecurityLevelId(IntEnum):
    """The previous security level of the entity

    See: https://schema.ocsf.io/1.2.0/data_types/prev_security_level_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_99 = 99  # The security level is not mapped. See the <code>prev_security_level</code> attribute, which contains data source specific values.
