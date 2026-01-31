"""<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events. enumeration."""

from enum import IntEnum


class SeverityId(IntEnum):
    """<p>The normalized identifier of the event/finding severity.</p>The normalized severity is a measurement the effort and expense required to manage and resolve an event or incident. Smaller numerical values represent lower impact events, and larger numerical values represent higher impact events.

    See: https://schema.ocsf.io/1.1.0/data_types/severity_id
    """

    VALUE_0 = 0  # The event/finding severity is unknown.
    VALUE_1 = 1  # Informational message. No action required.
    VALUE_2 = 2  # The user decides if action is needed.
    VALUE_3 = 3  # Action is required but the situation is not serious at this time.
    VALUE_4 = 4  # Action is required immediately.
    VALUE_5 = 5  # Action is required immediately and the scope is broad.
    VALUE_6 = 6  # An error occurred but it is too late to take remedial action.
    VALUE_99 = 99  # The event/finding severity is not mapped. See the <code>severity</code> attribute, which contains a data source specific value.
