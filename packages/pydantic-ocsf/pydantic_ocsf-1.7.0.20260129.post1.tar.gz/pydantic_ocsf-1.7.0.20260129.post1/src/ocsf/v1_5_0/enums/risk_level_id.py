"""The normalized risk level id. enumeration."""

from enum import IntEnum


class RiskLevelId(IntEnum):
    """The normalized risk level id.

    See: https://schema.ocsf.io/1.5.0/data_types/risk_level_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_4 = 4  #
    VALUE_99 = 99  # The risk level is not mapped. See the <code>risk_level</code> attribute, which contains a data source specific value.
