# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class PaymentPage(TypedDict, total=False):
    """Type of payment page."""
    type: Optional[Literal["subscription"]]
    """ID of the payment page."""
    id: Optional[str]
    """URL to redirect to after payment completion."""
    return_url: Optional[str]
    """Name of the payment page."""
    name: Optional[str]
    """URL-friendly identifier for the payment page."""
    slug: Optional[str]
    """Description of the payment page."""
    description: Optional[str]
    """Represents the object's type."""
    object: Optional[Literal["payment_page"]]
    """Public URL for the payment page."""
    hosted_url: Optional[str]
    """Status of the payment page."""
    status: Optional[Literal["draft", "active", "archived"]]
    """Timestamp indicating when the object was created."""
    created_at: Optional[str]
