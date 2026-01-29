# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal

from .meter_profile import MeterProfile


class MeterUpdate(TypedDict, total=False):
    """The name of the event to track usage for."""
    event_name: Optional[str]
    """Name of the meter."""
    name: Optional[str]
    """Internal description of the meter."""
    description: Optional[str]
    """Defines the connection between event data and Billingrails accounts."""
    account_mapping: Optional[dict]
    """Meter profiles define aggregation behaviors for a meter."""
    profiles: Optional[List[MeterProfile]]
