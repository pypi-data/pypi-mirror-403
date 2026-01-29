# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal

from .interval import Interval
from .fee_input import FeeInput
from .price import Price


class PlanCreate(TypedDict, total=False):
    """Number of billing cycles for this fee."""
    billing_cycles: Optional[int]
    """Billing interval for the plan."""
    interval: Interval
    """Name of the plan."""
    name: str
    """Internal identifier of the plan."""
    code: str
    """Description of the plan."""
    description: Optional[str]
    """When to bill for this fee."""
    bill_timing: Optional[Literal["advance", "arrears"]]
    """Trial period of the plan in days."""
    trial_period_days: Optional[int]
    """Number of free units included."""
    free_units: Optional[int]
    """Price object for the plan."""
    price: Price
    """Fees associated with the plan."""
    fees: Optional[List[FeeInput]]
    """Name that appears on invoices for this plan."""
    invoice_name: Optional[str]
