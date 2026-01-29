# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class DiscountInput(TypedDict, total=False):
    """Date when the discount expires."""
    valid_until: Optional[str]
    """Additional data related to the discount."""
    metadata: Optional[dict]
    """Maximum number of billing periods discount can recur (null = forever)."""
    max_recurring_intervals: Optional[int]
    """Whether discount can be applied to multiple billing periods."""
    recurring: Optional[bool]
    """Name of the discount."""
    name: Optional[str]
    """Maximum number of redemptions per account."""
    max_redemptions_per_account: Optional[int]
    """Date when the discount becomes valid."""
    valid_from: Optional[str]
    """Description of the discount."""
    description: Optional[str]
    """Currency. Required when type is `fixed_amount`."""
    currency: Optional[str]
    """Percentage off. Required when type is `percentage`."""
    percent_off: Optional[int]
    """Amount off in currency subunits. Required when type is `fixed_amount`."""
    amount_off: Optional[int]
    """Type of discount."""
    type: Optional[Literal["percentage", "fixed_amount"]]
    """Maximum number of redemptions across all accounts."""
    max_redemptions: Optional[int]
