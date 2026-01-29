# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class PaymentRequest(TypedDict, total=False):
    """ID of the payment request."""
    id: Optional[str]
    """Number of days until the payment request is due."""
    due_in_days: Optional[int]
    """Represents the object's type."""
    object: Optional[Literal["payment_request"]]
    """Type of payment request."""
    type: Optional[str]
    """Order of this payment request."""
    ordinal: Optional[int]
    """Status of the payment request."""
    status: Optional[str]
    """Date the payment request is due."""
    due_at: Optional[str]
    """Amount due in the payment request."""
    due_amount: Optional[int]
    """Currency of the payment request."""
    currency: Optional[str]
