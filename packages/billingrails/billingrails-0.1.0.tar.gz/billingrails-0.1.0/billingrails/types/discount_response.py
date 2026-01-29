# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional

from .discount import Discount


class DiscountResponse(TypedDict, total=False):
    discount: Optional[Discount]
    meta: Optional[dict]
