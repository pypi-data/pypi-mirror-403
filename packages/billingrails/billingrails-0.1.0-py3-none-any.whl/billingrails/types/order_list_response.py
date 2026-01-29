# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .order import Order


class OrderListResponse(TypedDict, total=False):
    orders: Optional[List[Order]]
    meta: Optional[dict]
