# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal


class MeterProfile(TypedDict, total=False):
    """Specifies the method for aggregating matching events."""
    aggregation_method: Literal["sum", "count", "count_unique", "min", "max", "latest"]
    """ID of the profile."""
    id: Optional[str]
    """A key that specifies which event property is used to aggregate data. Not required for `count` aggregation method."""
    aggregation_property: Optional[str]
    """Name of the meter profile."""
    name: str
    """Code identifier of the meter profile."""
    code: str
    """Time window for aggregation."""
    aggregation_time_window: Optional[Literal["hour", "day"]]
    """Whether the profile tracks recurring usage."""
    recurring: bool
    """Filters to apply to events for this profile."""
    filters: Optional[List[dict]]
