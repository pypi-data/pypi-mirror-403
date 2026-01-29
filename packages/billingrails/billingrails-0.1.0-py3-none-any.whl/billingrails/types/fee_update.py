# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal

from .price import Price
from .interval import Interval


class FeeUpdate(TypedDict, total=False):
    """Feature entitlements associated with this fee."""
    entitlements: Optional[List[dict]]
    """Name that appears on invoices for this fee."""
    invoice_name: Optional[str]
    """Plan ID or code associated with the fee."""
    plan_id: Optional[str]
    """Description of the fee."""
    description: Optional[str]
    """Unique code for the fee."""
    code: Optional[str]
    """Number of free units included."""
    free_units: Optional[int]
    """When to bill for this fee."""
    bill_timing: Optional[Literal["advance", "arrears"]]
    """Price configuration for the fee."""
    price: Optional[Price]
    """Meter profile ID to use for this fee."""
    meter_profile_id: Optional[str]
    """Number of billing cycles for this fee."""
    billing_cycles: Optional[int]
    """Billing interval for the fee."""
    interval: Optional[Interval]
    """Name of the fee."""
    name: Optional[str]
    """Meter ID for usage-based billing."""
    meter_id: Optional[str]
