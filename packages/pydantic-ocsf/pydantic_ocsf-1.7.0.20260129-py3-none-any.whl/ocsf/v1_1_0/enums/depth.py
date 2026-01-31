"""The CVSS depth represents a depth of the equation used to calculate CVSS score. enumeration."""

from enum import IntEnum


class Depth(IntEnum):
    """The CVSS depth represents a depth of the equation used to calculate CVSS score.

    See: https://schema.ocsf.io/1.1.0/data_types/depth
    """
