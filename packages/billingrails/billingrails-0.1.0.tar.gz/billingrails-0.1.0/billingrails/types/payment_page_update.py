# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class PaymentPageUpdate(TypedDict, total=False):
    """URL-friendly identifier for the payment page."""
    slug: Optional[str]
    """Description of the payment page."""
    description: Optional[str]
    """Type of payment page."""
    type: Optional[Literal["subscription"]]
    """Status of the payment page."""
    status: Optional[Literal["draft", "active", "archived"]]
    """ID of the plan associated with the payment page. Required if type is `subscription`."""
    plan_id: Optional[str]
    """Name of the payment page."""
    name: Optional[str]
