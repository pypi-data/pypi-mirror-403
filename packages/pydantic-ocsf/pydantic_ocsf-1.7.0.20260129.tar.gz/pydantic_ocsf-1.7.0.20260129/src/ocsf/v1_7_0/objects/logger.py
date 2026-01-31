"""Logger object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_7_0.objects.device import Device
    from ocsf.v1_7_0.objects.product import Product


class Logger(OCSFBaseModel):
    """The Logger object represents the device and product where events are stored with times for receipt and transmission.  This may be at the source device where the event occurred, a remote scanning device, intermediate hops, or the ultimate destination.

    See: https://schema.ocsf.io/1.7.0/objects/logger
    """

    device: Device | None = Field(
        default=None, description="The device where the events are logged. [Recommended]"
    )
    event_uid: str | None = Field(
        default=None, description="The unique identifier of the event assigned by the logger."
    )
    is_truncated: bool | None = Field(
        default=None,
        description="Indicates whether the OCSF event data has been truncated due to size limitations. When <code>true</code>, some event data may have been omitted to fit within system constraints.",
    )
    log_format: str | None = Field(
        default=None, description="The format of data in the log. For example JSON, syslog or CSV."
    )
    log_level: str | None = Field(
        default=None,
        description="The level at which an event was logged. This can be log provider specific. For example the audit level.",
    )
    log_name: str | None = Field(
        default=None,
        description="The log name for the logging provider log, or the file name of the system log. This may be an intermediate store-and-forward log or a vendor destination log. For example /archive/server1/var/log/messages.0 or /var/log/. [Recommended]",
    )
    log_provider: str | None = Field(
        default=None,
        description="The logging provider or logging service that logged the event. This may be an intermediate application store-and-forward log or a vendor destination log. [Recommended]",
    )
    log_version: str | None = Field(
        default=None,
        description="The event log schema version of the original event. For example the syslog version or the Cisco Log Schema version",
    )
    logged_time: int | None = Field(
        default=None,
        description="<p>The time when the logging system collected and logged the event.</p>This attribute is distinct from the event time in that event time typically contain the time extracted from the original event. Most of the time, these two times will be different. [Recommended]",
    )
    name: str | None = Field(
        default=None, description="The name of the logging product instance. [Recommended]"
    )
    product: Product | None = Field(
        default=None,
        description="The product logging the event.  This may be the event source product, a management server product, a scanning product, a SIEM, etc. [Recommended]",
    )
    transmit_time: int | None = Field(
        default=None,
        description="The time when the event was transmitted from the logging device to it's next destination. [Recommended]",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the logging product instance. [Recommended]",
    )
    untruncated_size: int | None = Field(
        default=None,
        description="The original size of the OCSF event data in kilobytes before any truncation occurred. This field is typically populated when <code>is_truncated</code> is <code>true</code> to indicate the full size of the original event.",
    )
    version: str | None = Field(default=None, description="The version of the logging provider.")
