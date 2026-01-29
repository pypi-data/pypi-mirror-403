# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal


class Order(TypedDict, total=False):
    """ID of the object."""
    id: Optional[str]
    """Subtotal amount of the order."""
    subtotal_amount: Optional[int]
    """Timestamp indicating when the object was created."""
    created_at: Optional[str]
    """Paid amount of the order."""
    paid_amount: Optional[int]
    """Order number."""
    number: Optional[str]
    """Line items in the order."""
    line_items: Optional[List[dict]]
    """Payment status of the order."""
    payment_status: Optional[Literal["pending", "paid", "partially_paid", "refunded", "failed"]]
    """Return status of the order."""
    return_status: Optional[Literal["none", "requested", "approved", "returned"]]
    """Additional data related to the order."""
    metadata: Optional[dict]
    """Represents the object's type."""
    object: Optional[Literal["order"]]
    """Status of the order."""
    status: Optional[Literal["draft", "pending", "confirmed", "fulfilled", "canceled"]]
    """Outstanding amount of the order."""
    outstanding_amount: Optional[int]
    """Total amount of the order."""
    total_amount: Optional[int]
    """Fulfillment status of the order."""
    fulfillment_status: Optional[Literal["pending", "fulfilled", "partially_fulfilled", "canceled"]]
    """Account ID associated with the order."""
    account_id: Optional[str]
    """Currency of the order."""
    currency: Optional[str]
