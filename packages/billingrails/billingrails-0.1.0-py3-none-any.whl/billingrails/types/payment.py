# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal

from .payment_method import PaymentMethod


class Payment(TypedDict, total=False):
    payment_method: Optional[PaymentMethod]
    """Represents the object's type."""
    object: Optional[Literal["payment"]]
    """Amount of the payment."""
    amount: Optional[int]
    """ID of the account the payment belongs to."""
    account_id: Optional[str]
    """ID of the payment."""
    id: Optional[str]
    """Date the payment was created."""
    created_at: Optional[str]
    """Reference for the payment."""
    reference_id: Optional[str]
    """Status of the payment."""
    status: Optional[Literal["pending", "succeeded", "failed", "canceled"]]
    """Description of the payment."""
    description: Optional[str]
    """ID of the payment method used."""
    payment_method_id: Optional[str]
    """Currency of the payment."""
    currency: Optional[str]
