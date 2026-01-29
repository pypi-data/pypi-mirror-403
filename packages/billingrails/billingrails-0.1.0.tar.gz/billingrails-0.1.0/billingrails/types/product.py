# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class Product(TypedDict, total=False):
    """Status of the product."""
    status: Optional[Literal["active", "inactive"]]
    """Amount of the product in cents."""
    amount: Optional[int]
    """ID of the object."""
    id: Optional[str]
    """Model of the product."""
    model: Optional[str]
    """SKU of the product."""
    sku: Optional[str]
    """Vendor of the product."""
    vendor: Optional[str]
    """Unique code of the product."""
    code: Optional[str]
    """Represents the object's type."""
    object: Optional[Literal["product"]]
    """Currency of the product."""
    currency: Optional[str]
    """Description of the product."""
    description: Optional[str]
    """Name of the product."""
    name: Optional[str]
    """Timestamp indicating when the object was created."""
    created_at: Optional[str]
    """URL of the product image."""
    image_url: Optional[str]
