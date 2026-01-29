# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .product import Product


class ProductListResponse(TypedDict, total=False):
    products: Optional[List[Product]]
    meta: Optional[dict]
