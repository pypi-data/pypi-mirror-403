# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .discount import Discount


class DiscountListResponse(TypedDict, total=False):
    meta: Optional[dict]
    discounts: Optional[List[Discount]]
