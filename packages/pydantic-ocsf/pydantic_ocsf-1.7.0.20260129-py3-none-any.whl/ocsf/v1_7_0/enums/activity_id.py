"""The normalized identifier of the activity that triggered the event. enumeration."""

from enum import IntEnum


class ActivityId(IntEnum):
    """The normalized identifier of the activity that triggered the event.

    See: https://schema.ocsf.io/1.7.0/data_types/activity_id
    """

    VALUE_1 = 1  # The API call in the event pertains to a 'create' activity.
    VALUE_2 = 2  # The API call in the event pertains to a 'read' activity.
    VALUE_3 = 3  # The API call in the event pertains to a 'update' activity.
    VALUE_4 = 4  # The API call in the event pertains to a 'delete' activity.
