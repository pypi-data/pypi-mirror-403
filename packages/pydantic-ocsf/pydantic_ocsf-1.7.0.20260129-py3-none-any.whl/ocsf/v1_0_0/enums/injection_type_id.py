"""The normalized identifier of the process injection method. enumeration."""

from enum import IntEnum


class InjectionTypeId(IntEnum):
    """The normalized identifier of the process injection method.

    See: https://schema.ocsf.io/1.0.0/data_types/injection_type_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_99 = 99  #
