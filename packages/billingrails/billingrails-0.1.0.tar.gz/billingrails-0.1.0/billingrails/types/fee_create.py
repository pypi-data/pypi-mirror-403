# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal

from .interval import Interval
from .price import Price


class FeeCreate(TypedDict, total=False):
    """Name of the fee."""
    name: str
    """Description of the fee."""
    description: Optional[str]
    """Number of billing cycles for this fee."""
    billing_cycles: Optional[int]
    """Meter profile ID to use for this fee."""
    meter_profile_id: Optional[str]
    """When to bill for this fee."""
    bill_timing: Optional[Literal["advance", "arrears"]]
    """Price configuration for the fee."""
    price: Price
    """Plan ID or code associated with the fee."""
    plan_id: str
    """Number of free units included."""
    free_units: Optional[int]
    """Billing interval for the fee."""
    interval: Optional[Interval]
    """Feature entitlements associated with this fee."""
    entitlements: Optional[List[dict]]
    """Name that appears on invoices for this fee."""
    invoice_name: Optional[str]
    """Unique code for the fee."""
    code: str
    """Meter ID for usage-based billing."""
    meter_id: Optional[str]
