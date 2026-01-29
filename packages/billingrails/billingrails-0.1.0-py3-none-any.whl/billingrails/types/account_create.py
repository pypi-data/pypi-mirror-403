# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal

from .address import Address


class AccountCreate(TypedDict, total=False):
    """Country of the account."""
    country: Optional[str]
    """Billing address of the account."""
    billing_address: Optional[Address]
    """Additional data related to the account."""
    metadata: Optional[dict]
    """Timezone for the account."""
    timezone: Optional[str]
    """Email of the account."""
    email: str
    """Invoice settings for the account."""
    invoice_settings: Optional[dict]
    """Type of account."""
    type: Optional[Literal["individual", "organization"]]
    """Shipping address of the account."""
    shipping_address: Optional[Address]
    """Name of the account."""
    name: str
    """External unique reference ID or identifier for this account."""
    external_id: Optional[str]
    """Default currency of the account."""
    default_currency: Optional[str]
