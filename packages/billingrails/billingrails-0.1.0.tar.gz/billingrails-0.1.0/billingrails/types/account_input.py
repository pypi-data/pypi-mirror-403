# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal

from .address import Address


class AccountInput(TypedDict, total=False):
    """Email of the account."""
    email: Optional[str]
    """Type of account."""
    type: Optional[Literal["individual", "organization"]]
    """Invoice settings for the account."""
    invoice_settings: Optional[dict]
    """Additional data related to the account."""
    metadata: Optional[dict]
    """Shipping address of the account."""
    shipping_address: Optional[Address]
    """Name of the account."""
    name: Optional[str]
    """Country of the account."""
    country: Optional[str]
    """Default currency of the account."""
    default_currency: Optional[str]
    """External unique reference ID or identifier for this account."""
    external_id: Optional[str]
    """Timezone for the account."""
    timezone: Optional[str]
    """Billing address of the account."""
    billing_address: Optional[Address]
