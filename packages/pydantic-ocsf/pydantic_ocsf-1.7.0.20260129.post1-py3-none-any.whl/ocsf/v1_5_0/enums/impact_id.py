"""The normalized impact of the incident or finding. Per NIST, this is the magnitude of harm that can be expected to result from the consequences of unauthorized disclosure, modification, destruction, or loss of information or information system availability. enumeration."""

from enum import IntEnum


class ImpactId(IntEnum):
    """The normalized impact of the incident or finding. Per NIST, this is the magnitude of harm that can be expected to result from the consequences of unauthorized disclosure, modification, destruction, or loss of information or information system availability.

    See: https://schema.ocsf.io/1.5.0/data_types/impact_id
    """

    VALUE_0 = 0  # The normalized impact is unknown.
    VALUE_1 = 1  # The magnitude of harm is low.
    VALUE_2 = 2  # The magnitude of harm is moderate.
    VALUE_3 = 3  # The magnitude of harm is high.
    VALUE_4 = 4  # The magnitude of harm is high and the scope is widespread.
    VALUE_99 = 99  # The impact is not mapped. See the <code>impact</code> attribute, which contains a data source specific value.
