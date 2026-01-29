# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .payment_page import PaymentPage


class PaymentPageListResponse(TypedDict, total=False):
    payment_pages: Optional[List[PaymentPage]]
    meta: Optional[dict]
