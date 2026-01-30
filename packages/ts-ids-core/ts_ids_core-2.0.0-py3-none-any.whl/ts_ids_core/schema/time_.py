from __future__ import annotations

from ts_ids_core.annotations import Nullable, Required
from ts_ids_core.base.ids_element import IdsElement
from ts_ids_core.base.ids_field import IdsField


class RawTime(IdsElement):
    """The base model for capturing common time fields found in primary data."""

    start: Nullable[str] = IdsField(description="Process/experiment/task start time.")
    created: Nullable[str] = IdsField(description="Data created time.")
    stop: Nullable[str] = IdsField(
        description="Process/experiment/task stop/finish time."
    )
    duration: Nullable[str] = IdsField(description="Process/experiment/task duration.")
    last_updated: Nullable[str] = IdsField(
        description="Data last updated time of a file/method."
    )
    acquired: Nullable[str] = IdsField(
        description="Data acquired/exported/captured time."
    )
    modified: Nullable[str] = IdsField(description="Data last modified/edited time.")
    lookup: Nullable[str] = IdsField(description="Data lookup time.")


class Time(RawTime):
    """A model for datetime values converted to a standard ISO format and their
    respective raw datetime values in the primary data.
    """

    raw: RawTime = IdsField(description="Raw time values from primary data.")


class RawSampleTime(RawTime):
    """The base model for time associated with a specific sample."""

    lookup: Required[Nullable[str]] = IdsField(
        description="Raw sample data lookup time."
    )


class SampleTime(RawSampleTime):
    """
    A model for experiment sample datetime values converted to a standard ISO format
    and their respective raw datetime values in the primary data.
    """

    raw: RawSampleTime = IdsField(
        description="Raw sample time values from primary data."
    )
