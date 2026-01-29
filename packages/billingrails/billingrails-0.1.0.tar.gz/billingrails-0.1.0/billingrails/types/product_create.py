# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class ProductCreate(TypedDict, total=False):
    """Status of the product."""
    status: Literal["active", "inactive"]
    """Name of the product."""
    name: str
    """Currency of the product."""
    currency: str
    """Amount of the product in cents."""
    amount: int
    """Description of the product."""
    description: Optional[str]
    """Unique code of the product."""
    code: str
    """URL of the product image."""
    image_url: Optional[str]
    """SKU of the product."""
    sku: Optional[str]
    """Model of the product."""
    model: str
