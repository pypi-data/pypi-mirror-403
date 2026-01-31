"""Describes the normalized status of DNS Security Extensions (DNSSEC) for a domain. enumeration."""

from enum import IntEnum


class DnssecStatusId(IntEnum):
    """Describes the normalized status of DNS Security Extensions (DNSSEC) for a domain.

    See: https://schema.ocsf.io/1.7.0/data_types/dnssec_status_id
    """

    VALUE_0 = 0  # The disposition is unknown.
    VALUE_1 = 1  # The related domain enables the signing of DNS records using DNSSEC.
    VALUE_2 = 2  # The related domain does not enable the signing of DNS records using DNSSEC.
    VALUE_99 = 99  # The DNSSEC status is not mapped. See the <code>dnssec_status</code> attribute, which contains a data source specific value.
