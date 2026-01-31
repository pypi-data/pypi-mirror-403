"""The normalized identifier of the DNS server response code. See <a target='_blank' href='https://datatracker.ietf.org/doc/html/rfc6895'>RFC-6895</a>. enumeration."""

from enum import IntEnum


class RcodeId(IntEnum):
    """The normalized identifier of the DNS server response code. See <a target='_blank' href='https://datatracker.ietf.org/doc/html/rfc6895'>RFC-6895</a>.

    See: https://schema.ocsf.io/1.0.0/data_types/rcode_id
    """

    VALUE_0 = 0  # No Error.
    VALUE_1 = 1  # Format Error.
    VALUE_2 = 2  # Server Failure.
    VALUE_3 = 3  # Non-Existent Domain.
    VALUE_4 = 4  # Not Implemented.
    VALUE_5 = 5  # Query Refused.
    VALUE_6 = 6  # Name Exists when it should not.
    VALUE_7 = 7  # RR Set Exists when it should not.
    VALUE_8 = 8  # RR Set that should exist does not.
    VALUE_9 = 9  # Not Authorized or Server Not Authoritative for zone.
    VALUE_10 = 10  # Name not contained in zone.
    VALUE_11 = 11  # DSO-TYPE Not Implemented.
    VALUE_16 = 16  # TSIG Signature Failure or Bad OPT Version.
    VALUE_17 = 17  # Key not recognized.
    VALUE_18 = 18  # Signature out of time window.
    VALUE_19 = 19  # Bad TKEY Mode.
    VALUE_20 = 20  # Duplicate key name.
    VALUE_21 = 21  # Algorithm not supported.
    VALUE_22 = 22  # Bad Truncation.
    VALUE_23 = 23  # Bad/missing Server Cookie.
    VALUE_24 = 24  # The codes deemed to be unassigned by the RFC (unassigned codes: 12-15, 24-3840, 4096-65534).
    VALUE_25 = 25  # The codes deemed to be reserved by the RFC (codes: 3841-4095, 65535).
    VALUE_99 = 99  # The dns response code is not defined by the RFC.
