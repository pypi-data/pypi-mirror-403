# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class CreditGrant(TypedDict, total=False):
    """Date when the credit grant expires."""
    expires_at: Optional[str]
    """Status of the credit grant."""
    status: Optional[Literal["pending", "granted", "depleted", "expired", "voided"]]
    """Granted amount in cents or quantity of credit assets."""
    grant_amount: Optional[int]
    """Timestamp indicating when the object was created."""
    created_at: Optional[str]
    """Payment status of the credit grant."""
    payment_status: Optional[Literal["comped", "paid", "unpaid"]]
    """ID of the object."""
    id: Optional[str]
    """Type of credit grant."""
    type: Optional[Literal["paid", "promotional", "refund"]]
    """Available amount in cents or quantity of credit assets."""
    available_amount: Optional[int]
    """Currency of the credit grant."""
    currency: Optional[str]
    """Account ID associated with the credit grant."""
    account_id: Optional[str]
    """Date when the credit grant becomes effective."""
    effective_at: Optional[str]
    """Represents the object's type."""
    object: Optional[Literal["credit_grant"]]
