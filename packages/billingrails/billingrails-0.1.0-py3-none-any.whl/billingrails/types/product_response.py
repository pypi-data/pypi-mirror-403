# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional

from .product import Product


class ProductResponse(TypedDict, total=False):
    product: Optional[Product]
    meta: Optional[dict]
