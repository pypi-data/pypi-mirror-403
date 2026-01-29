# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional

from .payment_page import PaymentPage


class PaymentPageResponse(TypedDict, total=False):
    payment_page: Optional[PaymentPage]
    meta: Optional[dict]
