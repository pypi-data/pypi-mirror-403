# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional

from .subscription import Subscription


class SubscriptionResponse(TypedDict, total=False):
    meta: Optional[dict]
    subscription: Optional[Subscription]
