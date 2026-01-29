# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal


"""Price configuration for a plan or fee."""
class Price(TypedDict, total=False):
    """Flat amount added to percentage model."""
    flat_amount: Optional[int]
    """Currency code."""
    currency: str
    """Pricing tiers (for volume and graduated models)."""
    tiers: Optional[List[dict]]
    """Package size (for package model)."""
    package_size: Optional[int]
    """Amount in currency subunits (for flat, package, or tiered pricing)."""
    amount: Optional[int]
    """Pricing model."""
    model: Literal["flat", "package", "volume", "graduated", "percentage"]
    """Percentage rate (for percentage model)."""
    percentage_rate: Optional[int]
