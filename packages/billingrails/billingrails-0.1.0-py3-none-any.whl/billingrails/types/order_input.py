# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .address import Address


class OrderInput(TypedDict, total=False):
    """Shipping address of the order."""
    shipping_address: Optional[Address]
    """Additional data related to the order."""
    metadata: Optional[dict]
    """Currency of the order."""
    currency: Optional[str]
    """Whether to use billing address for shipping."""
    use_billing_address_for_shipping: Optional[bool]
    """Line items in the order."""
    line_items: Optional[List[dict]]
    """Billing address of the order."""
    billing_address: Optional[Address]
    """Account ID associated with the order."""
    account_id: Optional[str]
