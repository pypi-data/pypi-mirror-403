# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .address import Address


class OrderCreate(TypedDict, total=False):
    """Whether to use billing address for shipping."""
    use_billing_address_for_shipping: Optional[bool]
    """Shipping address of the order."""
    shipping_address: Optional[Address]
    """Line items in the order."""
    line_items: List[dict]
    """Additional data related to the order."""
    metadata: Optional[dict]
    """Currency of the order."""
    currency: str
    """Billing address of the order."""
    billing_address: Optional[Address]
    """Account ID associated with the order."""
    account_id: str
