# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal

from .address import Address


class Account(TypedDict, total=False):
    """Represents the object's type."""
    object: Optional[Literal["account"]]
    """ID of the object."""
    id: Optional[str]
    """Type of account."""
    type: Optional[Literal["individual", "organization"]]
    """Invoice settings for the account."""
    invoice_settings: Optional[dict]
    """Additional data related to the account."""
    metadata: Optional[dict]
    """Name of the account."""
    name: Optional[str]
    """Timezone for the account."""
    timezone: Optional[str]
    """Country of the account."""
    country: Optional[str]
    """Timestamp indicating when the object was created."""
    created_at: Optional[str]
    """Default currency of the account."""
    default_currency: Optional[str]
    """External ID of the object."""
    external_id: Optional[str]
    """Shipping address of the account."""
    shipping_address: Optional[Address]
    """Billing address of the account."""
    billing_address: Optional[Address]
    """Email of the account."""
    email: Optional[str]
