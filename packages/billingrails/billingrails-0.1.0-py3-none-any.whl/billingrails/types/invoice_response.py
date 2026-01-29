# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional

from .invoice import Invoice


class InvoiceResponse(TypedDict, total=False):
    invoice: Optional[Invoice]
    meta: Optional[dict]
