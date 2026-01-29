# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional

from .event import Event


class EventResponse(TypedDict, total=False):
    meta: Optional[dict]
    event: Optional[Event]
