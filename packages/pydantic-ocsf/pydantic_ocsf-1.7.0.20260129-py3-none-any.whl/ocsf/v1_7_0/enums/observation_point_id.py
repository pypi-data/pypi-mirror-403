"""The normalized identifier of the observation point. The observation point identifier indicates whether the source network endpoint, destination network endpoint, or neither served as the observation point for the activity. enumeration."""

from enum import IntEnum


class ObservationPointId(IntEnum):
    """The normalized identifier of the observation point. The observation point identifier indicates whether the source network endpoint, destination network endpoint, or neither served as the observation point for the activity.

    See: https://schema.ocsf.io/1.7.0/data_types/observation_point_id
    """

    VALUE_0 = 0  # The observation point is unknown.
    VALUE_1 = 1  # The source network endpoint is the observation point.
    VALUE_2 = 2  # The destination network endpoint is the observation point.
    VALUE_3 = 3  # Neither the source nor destination network endpoint is the observation point.
    VALUE_4 = 4  # Both the source and destination network endpoint are the observation point. This typically occurs in localhost or internal communications where the source and destination are the same endpoint, often resulting in a <code>connection_info.direction</code> of <code>Local</code>.
    VALUE_99 = 99  # The observation point is not mapped. See the <code>observation_point</code> attribute for a data source specific value.
