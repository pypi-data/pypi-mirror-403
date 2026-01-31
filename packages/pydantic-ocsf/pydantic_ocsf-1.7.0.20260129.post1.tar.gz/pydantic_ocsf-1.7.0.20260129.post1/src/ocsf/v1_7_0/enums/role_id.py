"""The normalized identifier of the resource's role in the context of the event or finding. enumeration."""

from enum import IntEnum


class RoleId(IntEnum):
    """The normalized identifier of the resource's role in the context of the event or finding.

    See: https://schema.ocsf.io/1.7.0/data_types/role_id
    """

    VALUE_1 = 1  # The resource is the primary target or subject of the event/finding.
    VALUE_2 = 2  # The resource is acting as the initiator or performer in the context of the event/finding.
    VALUE_3 = 3  # The resource was impacted or affected by the event/finding.
    VALUE_4 = 4  # The resource is related to or associated with the event/finding.
