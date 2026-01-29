# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, Literal


class InvoiceInput(TypedDict, total=False):
    """Payment method ID to charge (required if collection_method is automatic)."""
    payment_method_id: Optional[str]
    """Date the invoice is due."""
    due_at: Optional[str]
    """Payment collection method for the invoice."""
    collection_method: Optional[Literal["automatic", "manual"]]
