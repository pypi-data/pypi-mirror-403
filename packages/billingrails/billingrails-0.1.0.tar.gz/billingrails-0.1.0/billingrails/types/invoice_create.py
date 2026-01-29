# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal


class InvoiceCreate(TypedDict, total=False):
    """Items in the invoice."""
    line_items: List[dict]
    """Payment collection method for the invoice."""
    collection_method: Literal["automatic", "manual"]
    """Currency of the invoice."""
    currency: str
    """Account ID associated with the invoice."""
    account_id: str
    """Payment method ID to charge (required if collection_method is automatic)."""
    payment_method_id: Optional[str]
    """Date the invoice is due."""
    due_at: str
