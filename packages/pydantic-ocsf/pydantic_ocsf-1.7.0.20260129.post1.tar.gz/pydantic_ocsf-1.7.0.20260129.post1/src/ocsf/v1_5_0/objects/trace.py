"""Trace object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_5_0.objects.service import Service
    from ocsf.v1_5_0.objects.span import Span


class Trace(OCSFBaseModel):
    """The trace object contains information about a distributed trace,  which is crucial for observability. Traces are made up of one or more spans, which are individual units of work in application activity. Traces track the journey of a request as it moves through various services in a system, capturing key details like timing, status, and dependencies at each step. Traces provide insights into system performance, helping to identify latency, bottlenecks, and issues in complex, distributed environments.

    See: https://schema.ocsf.io/1.5.0/objects/trace
    """

    uid: str = Field(
        ...,
        description="The unique identifier of the trace used in distributed systems and microservices architecture to track and correlate requests across various components of an application.",
    )
    duration: int | None = Field(
        default=None,
        description="The total time, in milliseconds, that the trace covers, calculated as the difference between start_time and end_time. This duration helps assess the overall performance of a request as it travels across various services, and is essential for identifying latency and potential bottlenecks within the distributed system. The trace duration may differ from individual span durations due to the propagation and processing times of the trace as it spans multiple components.",
    )
    end_time: int | None = Field(
        default=None,
        description="The end timestamp of the trace, essential for identifying latency and performance bottlenecks. Like the start time, this timestamp is normalized across the trace system to ensure consistency, even when events are recorded across distributed services with unsynchronized clocks. Normalized time allows for accurate trace duration calculations and helps observability tools track overall performance across services, regardless of the individual system time settings.",
    )
    flags: list[str] | None = Field(
        default=None,
        description="The flags associated with the trace, used to indicate specific properties or behaviors, such as whether the trace is sampled or if it has special handling. Flags help control how traces are processed, logged, and analyzed, providing valuable context for tracing and observability tools in identifying trace characteristics or specific tracking requirements.",
    )
    service: Service | None = Field(
        default=None,
        description="Identifies the service or component generating the trace, helping to track and correlate the flow of requests through various parts of a distributed system. This information is essential for understanding the role and performance of specific services within the broader context of system operations and for diagnosing issues across different components.",
    )
    span: Span | None = Field(
        default=None,
        description="Represents a single unit of work or operation within a distributed trace. A span typically tracks the execution of a request across a service, capturing important details such as the operation, timestamps, and status. Spans help break down the overall trace into smaller, manageable parts, enabling detailed analysis of the performance and behavior of specific operations within the system. They are crucial for understanding latency, dependencies, and bottlenecks in complex distributed systems.",
    )
    start_time: int | None = Field(
        default=None,
        description="The start timestamp of the trace, essential for identifying latency and performance bottlenecks. Like the end time, this timestamp is normalized across the trace system to ensure consistency, even when events are recorded across distributed services with unsynchronized clocks. Normalized time enables accurate trace duration calculations and helps observability tools track performance across services, regardless of the individual system time settings.",
    )
