"""Logger object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.objects.device import Device
    from ocsf.v1_2_0.objects.product import Product


class Logger(OCSFBaseModel):
    """The Logger object represents the device and product where events are stored with times for receipt and transmission.  This may be at the source device where the event occurred, a remote scanning device, intermediate hops, or the ultimate destination.

    See: https://schema.ocsf.io/1.2.0/objects/logger
    """

    device: Device | None = Field(
        default=None, description="The device where the events are logged. [Recommended]"
    )
    log_level: str | None = Field(
        default=None, description="The audit level at which an event was generated."
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
    name: str | None = Field(
        default=None, description="The name of the logging product instance. [Recommended]"
    )
    product: Product | None = Field(
        default=None,
        description="The product logging the event.  This may be the event source product, a management server product, a scanning product, a SIEM, etc. [Recommended]",
    )
    transmit_time: int | None = Field(
        default=None,
        description="The time when the event was transmitted from the logging device to it's next destination.",
    )
    uid: str | None = Field(
        default=None,
        description="The unique identifier of the logging product instance. [Recommended]",
    )
    version: str | None = Field(default=None, description="The version of the logging product.")
