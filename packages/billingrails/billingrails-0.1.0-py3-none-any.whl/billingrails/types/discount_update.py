# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class DiscountUpdate(TypedDict, total=False):
    """Name of the discount."""
    name: Optional[str]
    """Currency. Required when type is `fixed_amount`."""
    currency: Optional[str]
    """Maximum number of billing periods discount can recur (null = forever)."""
    max_recurring_intervals: Optional[int]
    """Date when the discount becomes valid."""
    valid_from: Optional[str]
    """Additional data related to the discount."""
    metadata: Optional[dict]
    """Whether discount can be applied to multiple billing periods."""
    recurring: Optional[bool]
    """Maximum number of redemptions per account."""
    max_redemptions_per_account: Optional[int]
    """Date when the discount expires."""
    valid_until: Optional[str]
    """Description of the discount."""
    description: Optional[str]
    """Percentage off. Required when type is `percentage`."""
    percent_off: Optional[int]
    """Amount off in currency subunits. Required when type is `fixed_amount`."""
    amount_off: Optional[int]
    """Type of discount."""
    type: Optional[Literal["percentage", "fixed_amount"]]
    """Maximum number of redemptions across all accounts."""
    max_redemptions: Optional[int]
