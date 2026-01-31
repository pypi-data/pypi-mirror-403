"""The normalized impact of the finding. enumeration."""

from enum import IntEnum


class ImpactId(IntEnum):
    """The normalized impact of the finding.

    See: https://schema.ocsf.io/1.0.0/data_types/impact_id
    """

    VALUE_0 = 0  #
    VALUE_1 = 1  #
    VALUE_2 = 2  #
    VALUE_3 = 3  #
    VALUE_4 = 4  #
    VALUE_99 = 99  # The detection impact is not mapped. See the <code>impact</code> attribute, which contains a data source specific value.
