"""Metadata object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_0_0.objects.extension import Extension
    from ocsf.v1_0_0.objects.product import Product


class Metadata(OCSFBaseModel):
    """The Metadata object describes the metadata associated with the event. Defined by D3FEND <a target='_blank' href='https://d3fend.mitre.org/dao/artifact/d3f:Metadata/'>d3f:Metadata</a>.

    See: https://schema.ocsf.io/1.0.0/objects/metadata
    """

    product: Product = Field(..., description="The product that reported the event.")
    version: str = Field(
        ...,
        description="The version of the OCSF schema, using Semantic Versioning Specification (<a target='_blank' href='https://semver.org'>SemVer</a>). For example: 1.0.0. Event consumers use the version to determine the available event attributes.",
    )
    correlation_uid: str | None = Field(
        default=None, description="The unique identifier used to correlate events."
    )
    event_code: str | None = Field(
        default=None,
        description="The Event ID or Code that the product uses to describe the event.",
    )
    extension: Extension | None = Field(
        default=None, description="The schema extension used to create the event."
    )
    labels: list[str] | None = Field(
        default=None,
        description='<p>The list of category labels attached to the event or specific attributes. Labels are user defined tags or aliases added at normalization time.</p>For example: <code>["network", "connection.ip:destination", "device.ip:source"]</code>',
    )
    log_name: str | None = Field(
        default=None,
        description="The event log name. For example, syslog file name or Windows logging subsystem: Security. [Recommended]",
    )
    log_provider: str | None = Field(
        default=None,
        description="The logging provider or logging service that logged the event. For example, Microsoft-Windows-Security-Auditing. [Recommended]",
    )
    log_version: str | None = Field(
        default=None,
        description="The event log schema version that specifies the format of the original event. For example syslog version or Cisco Log Schema Version.",
    )
    logged_time: int | None = Field(
        default=None,
        description="<p>The time when the logging system collected and logged the event.</p>This attribute is distinct from the event time in that event time typically contain the time extracted from the original event. Most of the time, these two times will be different.",
    )
    modified_time: int | None = Field(
        default=None, description="The time when the event was last modified or enriched."
    )
    original_time: str | None = Field(
        default=None,
        description="The original event time as reported by the event source. For example, the time in the original format from system event log such as Syslog on Unix/Linux and the System event file on Windows. Omit if event is generated instead of collected via logs. [Recommended]",
    )
    processed_time: int | None = Field(
        default=None, description="The event processed time, such as an ETL operation."
    )
    profiles: list[str] | None = Field(
        default=None, description="The list of profiles used to create the event."
    )
    sequence: int | None = Field(
        default=None,
        description="Sequence number of the event. The sequence number is a value available in some events, to make the exact ordering of events unambiguous, regardless of the event time precision.",
    )
    uid: str | None = Field(
        default=None,
        description="The logging system-assigned unique identifier of an event instance.",
    )
