# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal

from .address import Address


class AccountUpdate(TypedDict, total=False):
    """Email of the account."""
    email: Optional[str]
    """Type of account."""
    type: Optional[Literal["individual", "organization"]]
    """Default currency of the account."""
    default_currency: Optional[str]
    """Billing address of the account."""
    billing_address: Optional[Address]
    """Shipping address of the account."""
    shipping_address: Optional[Address]
    """External unique reference ID or identifier for this account."""
    external_id: Optional[str]
    """Invoice settings for the account."""
    invoice_settings: Optional[dict]
    """Name of the account."""
    name: Optional[str]
    """Country of the account."""
    country: Optional[str]
    """Timezone for the account."""
    timezone: Optional[str]
    """Additional data related to the account."""
    metadata: Optional[dict]
