# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal

from .price import Price
from .interval import Interval


class Fee(TypedDict, total=False):
    """Number of free units allowed for this fee."""
    free_units: Optional[int]
    """Price for the fee."""
    price: Optional[Price]
    """Meter ID associated with the fee (for usage billing)."""
    meter_id: Optional[str]
    """Meter profile name (for usage billing)."""
    meter_profile_name: Optional[str]
    """Meter name (for usage billing)."""
    meter_name: Optional[str]
    """Meter profile ID to use for this fee (for usage billing)."""
    meter_profile_id: Optional[str]
    """Description of the fee."""
    description: Optional[str]
    """Plan ID associated with the fee."""
    plan_id: Optional[str]
    """Billing cycles of the fee."""
    billing_cycles: Optional[int]
    """Invoice name of the fee."""
    invoice_name: Optional[str]
    """ID of the object."""
    id: Optional[str]
    """Unique code for this fee."""
    code: Optional[str]
    """Timestamp indicating when the object was created."""
    created_at: Optional[str]
    """Determines whether fee is billed in advance or arrears."""
    bill_timing: Optional[Literal["advance", "arrears"]]
    """Name of the fee."""
    name: Optional[str]
    """Represents the object's type."""
    object: Optional[Literal["fee"]]
    """Entitlements associated with the fee."""
    entitlements: Optional[List[dict]]
    """Billing interval for the fee."""
    interval: Optional[Interval]
