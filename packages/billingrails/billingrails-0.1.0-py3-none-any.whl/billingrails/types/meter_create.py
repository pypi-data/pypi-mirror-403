# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal

from .meter_profile import MeterProfile


class MeterCreate(TypedDict, total=False):
    """Internal description of the meter."""
    description: Optional[str]
    """Meter profiles define aggregation behaviors for a meter."""
    profiles: List[MeterProfile]
    """The name of the event to track usage for."""
    event_name: str
    """Defines the connection between event data and Billingrails accounts."""
    account_mapping: dict
    """Name of the meter."""
    name: str
