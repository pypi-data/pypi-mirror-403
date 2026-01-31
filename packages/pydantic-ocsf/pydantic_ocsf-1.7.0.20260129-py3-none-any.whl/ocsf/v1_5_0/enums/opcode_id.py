"""The DNS opcode ID specifies the normalized query message type as defined in <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc5395.html'>RFC-5395</a>. enumeration."""

from enum import IntEnum


class OpcodeId(IntEnum):
    """The DNS opcode ID specifies the normalized query message type as defined in <a target='_blank' href='https://www.rfc-editor.org/rfc/rfc5395.html'>RFC-5395</a>.

    See: https://schema.ocsf.io/1.5.0/data_types/opcode_id
    """

    VALUE_0 = 0  # Standard query
    VALUE_1 = 1  # Inverse query, obsolete
    VALUE_2 = 2  # Server status request
    VALUE_3 = 3  # Reserved, not used
    VALUE_4 = 4  # Zone change notification
    VALUE_5 = 5  # Dynamic DNS update
    VALUE_6 = 6  # DNS Stateful Operations (DSO)
    VALUE_99 = 99  # The DNS Opcode is not defined by the RFC. See the <code>opcode</code> attribute, which contains a data source specific value.
