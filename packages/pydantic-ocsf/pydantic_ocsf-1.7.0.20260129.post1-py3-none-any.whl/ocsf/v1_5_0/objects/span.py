"""Span object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.service import Service


class Span(OCSFBaseModel):
    """Represents a single unit of work or operation within a distributed trace. A span typically tracks the execution of a request across a service, capturing important details such as the operation, timestamps, and status. Spans help break down the overall trace into smaller, manageable parts, enabling detailed analysis of the performance and behavior of specific operations within the system. They are crucial for understanding latency, dependencies, and bottlenecks in complex distributed systems.

    See: https://schema.ocsf.io/1.5.0/objects/span
    """

    end_time: int = Field(
        ...,
        description="The end timestamp of the span, essential for identifying latency and performance bottlenecks. Like the start time, this timestamp is normalized across the observability system to ensure consistency, even when events are recorded across distributed services with unsynchronized clocks. Normalized time allows for accurate duration calculations and helps observability tools track performance across services, regardless of the individual system time settings.",
    )
    start_time: int = Field(
        ...,
        description="The start timestamp of the span, essential for identifying latency and performance bottlenecks. This timestamp is normalized across the observability system, ensuring consistency even when events occur across distributed services with potentially unsynchronized clocks. By using normalized time, observability tools can provide accurate, uniform measurements of operation performance and latency, regardless of where or when the events actually occur.",
    )
    uid: str = Field(
        ...,
        description="The unique identifier for the span, used in distributed systems and microservices architectures to track and correlate requests across different components of an application. It enables tracing the flow of a request through various services.",
    )
    duration: int | None = Field(
        default=None,
        description="The total time, in milliseconds, that the span represents, calculated as the difference between start_time and end_time. It reflects the operation's performance and latency, independent of event timestamps, and accounts for normalized times used by observability tools to ensure consistency across distributed systems.",
    )
    message: str | None = Field(
        default=None,
        description="The message in a span (often refered to as a span event) serves as a way to record significant moments or occurrences during the span's lifecycle. This content typically manifests as log entries, annotations, or semi-structured events as a string, providing additional granularity and context about what happens at specific points during the execution of an operation.",
    )
    operation: str | None = Field(
        default=None,
        description="Describes an action performed in a span, such as API requests, database queries, or computations.",
    )
    parent_uid: str | None = Field(
        default=None,
        description="The ID of the parent span for this span object, establishing its relationship in the trace hierarchy.",
    )
    service: Service | None = Field(
        default=None,
        description="Identifies the service or component that generates the span, helping trace its path through the distributed system.",
    )
    status_code: str | None = Field(
        default=None,
        description="Indicates the outcome of the operation in the span, such as success, failure, or error. Issues in a span typically refer to problems such as failed operations, timeouts, service unavailability, or errors in processing that can negatively impact the performance or reliability of the system. Tracking the `status_code` helps pinpoint these issues, enabling quicker identification and resolution of system inefficiencies or faults.",
    )
