# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class PaymentPageCreate(TypedDict, total=False):
    """Name of the payment page."""
    name: str
    """Status of the payment page."""
    status: Optional[Literal["draft", "active", "archived"]]
    """ID of the plan associated with the payment page. Required if type is `subscription`."""
    plan_id: Optional[str]
    """Type of payment page."""
    type: Literal["subscription"]
    """URL-friendly identifier for the payment page."""
    slug: Optional[str]
    """Unique code for the payment page."""
    code: str
    """Description of the payment page."""
    description: Optional[str]
