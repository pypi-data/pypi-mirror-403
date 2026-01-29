# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .event import Event


class EventBatchResponse(TypedDict, total=False):
    meta: Optional[dict]
    events: Optional[List[Event]]
