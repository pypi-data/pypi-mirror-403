# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal

from .fee import Fee
from .price import Price
from .interval import Interval


class Plan(TypedDict, total=False):
    """Meter ID associated with the fee (for usage billing)."""
    meter_id: Optional[str]
    """Billing cycles of the fee."""
    billing_cycles: Optional[int]
    """Description of the plan."""
    description: Optional[str]
    """Represents the object's type."""
    object: Optional[Literal["plan"]]
    """ID of the object."""
    id: Optional[str]
    """Number of free units allowed for this fee."""
    free_units: Optional[int]
    """Name that appears on invoices for this plan."""
    invoice_name: Optional[str]
    """Meter name (for usage billing)."""
    meter_name: Optional[str]
    """Name of the plan."""
    name: Optional[str]
    """Timestamp indicating when the object was created."""
    created_at: Optional[str]
    """Price for the plan."""
    price: Optional[Price]
    """Trial period of the plan in days."""
    trial_period_days: Optional[int]
    """Determines whether fee is billed in advance or arrears."""
    bill_timing: Optional[Literal["advance", "arrears"]]
    """Meter profile name (for usage billing)."""
    meter_profile_name: Optional[str]
    """Fees associated with the plan."""
    fees: Optional[List[Fee]]
    """Internal identifier of the plan."""
    code: Optional[str]
    """Billing interval for the plan."""
    interval: Optional[Interval]
    """Meter profile ID to use for this fee (for usage billing)."""
    meter_profile_id: Optional[str]
    """Status of the plan."""
    status: Optional[Literal["draft", "active", "archived"]]
