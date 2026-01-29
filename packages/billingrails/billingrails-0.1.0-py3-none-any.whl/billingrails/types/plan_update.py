# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal

from .interval import Interval
from .price import Price


class PlanUpdate(TypedDict, total=False):
    """Trial period of the plan in days."""
    trial_period_days: Optional[int]
    """Number of free units included."""
    free_units: Optional[int]
    """Billing interval for the plan."""
    interval: Optional[Interval]
    """Number of billing cycles for this fee."""
    billing_cycles: Optional[int]
    """Name that appears on invoices for this plan."""
    invoice_name: Optional[str]
    """Description of the plan."""
    description: Optional[str]
    """Name of the plan."""
    name: Optional[str]
    """When to bill for this fee."""
    bill_timing: Optional[Literal["advance", "arrears"]]
    """Price object for the plan."""
    price: Optional[Price]
