import textwrap
from datetime import datetime, timedelta
from typing import Any, List, Sequence

import temporalio.client
from pydantic import BaseModel, Field
from temporalio.client import ScheduleOverlapPolicy


class ScheduleRange(BaseModel, temporalio.client.ScheduleRange, frozen=True):
    """Inclusive range for a schedule match value."""

    start: int
    """Inclusive start of the range."""

    end: int = 0
    """Inclusive end of the range.

    If unset or less than start, defaults to start.
    """

    step: int = 0
    """
    Step to take between each value.

    Unset or 0 defaults as 1.
    """


class ScheduleInterval(BaseModel, temporalio.client.ScheduleIntervalSpec):
    """Specification for scheduling on an interval.

    Matches times expressed as epoch + (n * every) + offset.
    """

    every: timedelta
    """Period to repeat the interval."""

    offset: timedelta | None = None
    """Fixed offset added to each interval period."""


class ScheduleCalendar(BaseModel, temporalio.client.ScheduleCalendarSpec):
    """Specification relative to calendar time when to run an action.

    A timestamp matches if at least one range of each field matches except for
    year. If year is missing, that means all years match. For all fields besides
    year, at least one range must be present to match anything.
    """

    second: Sequence[ScheduleRange] = (ScheduleRange(start=0),)
    """Second range to match, 0-59. Default matches 0."""

    minute: Sequence[ScheduleRange] = (ScheduleRange(start=0),)
    """Minute range to match, 0-59. Default matches 0."""

    hour: Sequence[ScheduleRange] = (ScheduleRange(start=0),)
    """Hour range to match, 0-23. Default matches 0."""

    day_of_month: Sequence[ScheduleRange] = (ScheduleRange(start=1, end=31),)
    """Day of month range to match, 1-31. Default matches all days."""

    month: Sequence[ScheduleRange] = (ScheduleRange(start=1, end=12),)
    """Month range to match, 1-12. Default matches all months."""

    year: Sequence[ScheduleRange] = ()
    """Optional year range to match. Default of empty matches all years."""

    day_of_week: Sequence[ScheduleRange] = (ScheduleRange(start=0, end=6),)
    """Day of week range to match, 0-6, 0 is Sunday. Default matches all
    days."""

    comment: str | None = None
    """Description of this schedule."""


class SchedulePolicy(BaseModel):
    catchup_window_seconds: int = Field(
        default=31536000,
        description=(
            "After a Temporal server is unavailable, amount of time in seconds in the past to execute missed actions."
        ),
    )
    overlap: ScheduleOverlapPolicy = Field(
        default=ScheduleOverlapPolicy.SKIP,
        description="Policy controlling what to do when a workflow is already running.",
    )
    pause_on_failure: bool = Field(default=False, description="Whether to pause the schedule after a workflow failure.")

    @property
    def catchup_window(self) -> timedelta:
        return timedelta(seconds=self.catchup_window_seconds)

    @catchup_window.setter
    def catchup_window(self, value: timedelta) -> None:
        self.catchup_window_seconds = int(value.total_seconds())


class ScheduleDefinition(BaseModel):
    """Specification of the times scheduled actions may occur.

    The times are the union of :py:attr:`calendars`, :py:attr:`intervals`, and
    :py:attr:`cron_expressions` excluding anything in :py:attr:`skip`.
    """

    input: Any = Field(description="Input to provide to the workflow when starting it.")

    calendars: List[ScheduleCalendar] = Field(
        default_factory=list, description="Calendar-based specification of times."
    )

    intervals: List[ScheduleInterval] = Field(
        default_factory=list, description="Interval-based specification of times."
    )

    cron_expressions: List[str] = Field(default_factory=list, description="Cron-based specification of times.")

    skip: List[ScheduleCalendar] = Field(default_factory=list, description="Set of calendar times to skip.")

    start_at: datetime | None = Field(default=None, description="Time after which the first action may be run.")

    end_at: datetime | None = Field(default=None, description="Time after which no more actions will be run.")

    jitter: timedelta | None = Field(
        default=None,
        description=textwrap.dedent(
            """
            Jitter to apply each action.

            An action's scheduled time will be incremented by a random value between 0
            and this value if present (but not past the next schedule).
            """
        ),
    )

    time_zone_name: str | None = Field(default=None, description="IANA time zone name, for example ``US/Central``.")

    policy: SchedulePolicy = Field(default_factory=SchedulePolicy, description="Policy for the schedule.")
