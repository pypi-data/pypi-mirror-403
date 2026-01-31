"""The normalized identifier of the stratum level, as defined in <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc5905.html'>RFC-5905</a>. enumeration."""

from enum import IntEnum


class StratumId(IntEnum):
    """The normalized identifier of the stratum level, as defined in <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc5905.html'>RFC-5905</a>.

    See: https://schema.ocsf.io/1.5.0/data_types/stratum_id
    """

    VALUE_0 = 0  # Unspecified or invalid.
    VALUE_1 = 1  # The highest precision primary server (e.g atomic clock or GPS).
    VALUE_2 = 2  # A secondary level server (possible values: 2-15).
    VALUE_16 = 16  #
    VALUE_17 = 17  # Reserved stratum (possible values: 17-255).
    VALUE_99 = 99  # The stratum level is not mapped. See the <code>stratum</code> attribute, which contains a data source specific value.
