"""The normalized priority. Priority identifies the relative importance of the finding. It is a measurement of urgency. enumeration."""

from enum import IntEnum


class PriorityId(IntEnum):
    """The normalized priority. Priority identifies the relative importance of the finding. It is a measurement of urgency.

    See: https://schema.ocsf.io/1.2.0/data_types/priority_id
    """

    VALUE_0 = 0  # No priority is assigned.
    VALUE_1 = 1  # Application or personal procedure is unusable, where a workaround is available or a repair is possible.
    VALUE_2 = 2  # Non-critical function or procedure is unusable or hard to use causing operational disruptions with no direct impact on a service's availability. A workaround is available.
    VALUE_3 = 3  # Critical functionality or network access is interrupted, degraded or unusable, having a severe impact on services availability. No acceptable alternative is possible.
    VALUE_4 = 4  # Interruption making a critical functionality inaccessible or a complete network interruption causing a severe impact on services availability. There is no possible alternative.
    VALUE_99 = 99  # The priority is not normalized.
