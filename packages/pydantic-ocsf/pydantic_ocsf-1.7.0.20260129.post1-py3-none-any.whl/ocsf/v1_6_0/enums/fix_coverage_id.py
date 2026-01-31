"""The normalized identifier for fix coverage, applicable to this vulnerability. Typically useful, when there are multiple affected packages but only a subset have available fixes. enumeration."""

from enum import IntEnum


class FixCoverageId(IntEnum):
    """The normalized identifier for fix coverage, applicable to this vulnerability. Typically useful, when there are multiple affected packages but only a subset have available fixes.

    See: https://schema.ocsf.io/1.6.0/data_types/fix_coverage_id
    """

    VALUE_1 = 1  # All affected packages and components have available fixes or patches to remediate the vulnerability.
    VALUE_2 = 2  # Only some of the affected packages and components have available fixes or patches, while others remain vulnerable.
    VALUE_3 = 3  # No fixes or patches are currently available for any of the affected packages and components.
