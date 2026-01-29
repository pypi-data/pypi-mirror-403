# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional

from .order import Order


class OrderResponse(TypedDict, total=False):
    order: Optional[Order]
    meta: Optional[dict]
