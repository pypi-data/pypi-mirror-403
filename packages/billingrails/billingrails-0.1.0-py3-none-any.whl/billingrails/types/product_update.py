# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class ProductUpdate(TypedDict, total=False):
    """Name of the product."""
    name: Optional[str]
    """Unique code of the product."""
    code: Optional[str]
    """Description of the product."""
    description: Optional[str]
    """Model of the product."""
    model: Optional[str]
    """Currency of the product."""
    currency: Optional[str]
    """Status of the product."""
    status: Optional[Literal["active", "inactive"]]
    """URL of the product image."""
    image_url: Optional[str]
    """SKU of the product."""
    sku: Optional[str]
    """Amount of the product in cents."""
    amount: Optional[int]
