"""Specifies the type of detection pattern used to identify the associated threat indicator. enumeration."""

from enum import IntEnum


class DetectionPatternTypeId(IntEnum):
    """Specifies the type of detection pattern used to identify the associated threat indicator.

    See: https://schema.ocsf.io/1.5.0/data_types/detection_pattern_type_id
    """

    VALUE_0 = 0  # The type is not mapped.
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_4 = 4  #
    VALUE_5 = 5  #
    VALUE_6 = 6  #
    VALUE_99 = 99  # The detection pattern type is not mapped. See the <code>detection_pattern_type</code> attribute, which contains a data source specific value.
