# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .invoice import Invoice


class InvoiceListResponse(TypedDict, total=False):
    meta: Optional[dict]
    invoices: Optional[List[Invoice]]
