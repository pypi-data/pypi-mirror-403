# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional


class EventInput(TypedDict, total=False):
    """Properties associated with the event."""
    properties: dict
    """The name of the event."""
    event_name: str
    """Unique identifier for this event."""
    idempotency_key: Optional[str]
    """Timestamp indicating the occurrence of the event."""
    timestamp: Optional[str]
