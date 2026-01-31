"""Time Span object."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_6_0.enums.type_id import TypeId


class Timespan(OCSFBaseModel):
    """The Time Span object represents different time period durations. If a timespan is fractional, i.e. crosses one period, e.g. a week and 3 days, more than one may be populated since each member is of integral type. In that case <code>type_id</code> if present should be set to <code>Other.</code><P>A timespan may also be defined by its time interval boundaries, <code>start_time</code> and <code>end_time</code>.

    See: https://schema.ocsf.io/1.6.0/objects/timespan
    """

    duration: int | None = Field(
        default=None, description="The duration of the time span in milliseconds. [Recommended]"
    )
    duration_days: int | None = Field(
        default=None, description="The duration of the time span in days. [Recommended]"
    )
    duration_hours: int | None = Field(
        default=None, description="The duration of the time span in hours. [Recommended]"
    )
    duration_mins: int | None = Field(
        default=None, description="The duration of the time span in minutes. [Recommended]"
    )
    duration_months: int | None = Field(
        default=None, description="The duration of the time span in months. [Recommended]"
    )
    duration_secs: int | None = Field(
        default=None, description="The duration of the time span in seconds. [Recommended]"
    )
    duration_weeks: int | None = Field(
        default=None, description="The duration of the time span in weeks. [Recommended]"
    )
    duration_years: int | None = Field(
        default=None, description="The duration of the time span in years. [Recommended]"
    )
    end_time: int | None = Field(
        default=None,
        description="The end time or conclusion of the timespan's interval. [Recommended]",
    )
    start_time: int | None = Field(
        default=None,
        description="The start time or beginning of the timespan's interval. [Recommended]",
    )
    type_: str | None = Field(
        default=None, description="The type of time span duration the object represents."
    )
    type_id: TypeId | None = Field(
        default=None,
        description="The normalized identifier for the time span duration type. [Recommended]",
    )
