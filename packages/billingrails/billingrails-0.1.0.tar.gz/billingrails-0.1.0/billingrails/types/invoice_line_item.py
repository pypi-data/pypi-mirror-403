# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class InvoiceLineItem(TypedDict, total=False):
    """Unit amount of the invoice item."""
    unit_amount: Optional[int]
    """End date for the billing period."""
    billing_end: Optional[str]
    """Represents the object's type."""
    object: Optional[Literal["invoice_line_item"]]
    """Quantity of the invoice item."""
    quantity: Optional[int]
    """Description of the invoice item."""
    description: Optional[str]
    """Name of the invoice item."""
    name: Optional[str]
    """ID of the invoice item."""
    id: Optional[str]
    """Total amount of the invoice item."""
    total_amount: Optional[int]
    """Subtotal amount of the invoice item."""
    subtotal_amount: Optional[int]
    """Start date for the billing period."""
    billing_start: Optional[str]
