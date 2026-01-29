# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal

from .invoice_line_item import InvoiceLineItem
from .payment_request import PaymentRequest


class Invoice(TypedDict, total=False):
    """Subscription ID associated with the invoice."""
    subscription_id: Optional[str]
    """Total amount of the invoice including taxes, credits and discounts."""
    total_amount: Optional[int]
    """Credit amount applied to the invoice."""
    credit_amount: Optional[int]
    """URL to the hosted page of the invoice."""
    hosted_url: Optional[str]
    """Date the invoice is due."""
    due_at: Optional[str]
    """Date in the future when the invoice will be issued."""
    issue_at: Optional[str]
    """End date for the billing period."""
    billing_end: Optional[str]
    """Start date for the billing period."""
    billing_start: Optional[str]
    """Timestamp indicating when the object was created."""
    created_at: Optional[str]
    """Payment requests associated with this invoice."""
    payment_requests: Optional[List[PaymentRequest]]
    """Outstanding amount of the invoice."""
    outstanding_amount: Optional[int]
    """Status of the invoice."""
    status: Optional[Literal["pending", "draft", "issued", "overdue", "paid", "partially_paid", "refunded", "partially_refunded", "voided", "canceled", "failed"]]
    """Currency of the invoice."""
    currency: Optional[str]
    """Account ID associated with the invoice."""
    account_id: Optional[str]
    """Subtotal amount of the invoice excluding taxes, credits and discounts."""
    subtotal_amount: Optional[int]
    """Represents the object's type."""
    object: Optional[Literal["invoice"]]
    """Date the invoice was issued."""
    issued_at: Optional[str]
    """Amount written off from the invoice."""
    write_off_amount: Optional[int]
    """Items in the invoice."""
    line_items: Optional[List[InvoiceLineItem]]
    """Additional data related to the invoice."""
    metadata: Optional[dict]
    """Paid amount of the invoice."""
    paid_amount: Optional[int]
    """Type of invoice."""
    type: Optional[Literal["adhoc", "subscription_signup", "subscription_renewal", "subscription_update", "order"]]
    """Payment collection method for the invoice."""
    collection_method: Optional[Literal["manual", "automatic", "send_invoice"]]
    """Total amount currently due for this invoice."""
    due_amount: Optional[int]
    """URL to the PDF version of the invoice."""
    download_url: Optional[str]
    """Number of the invoice."""
    number: Optional[str]
    """ID of the object."""
    id: Optional[str]
