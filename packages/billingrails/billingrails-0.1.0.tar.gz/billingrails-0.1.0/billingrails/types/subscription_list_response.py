# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .subscription import Subscription


class SubscriptionListResponse(TypedDict, total=False):
    meta: Optional[dict]
    subscriptions: Optional[List[Subscription]]
