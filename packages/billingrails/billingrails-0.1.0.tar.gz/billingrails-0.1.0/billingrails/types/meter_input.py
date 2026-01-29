# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal

from .meter_profile import MeterProfile


class MeterInput(TypedDict, total=False):
    """Name of the meter."""
    name: Optional[str]
    """The name of the event to track usage for."""
    event_name: Optional[str]
    """Meter profiles define aggregation behaviors for a meter."""
    profiles: Optional[List[MeterProfile]]
    """Internal description of the meter."""
    description: Optional[str]
    """Defines the connection between event data and Billingrails accounts."""
    account_mapping: Optional[dict]
