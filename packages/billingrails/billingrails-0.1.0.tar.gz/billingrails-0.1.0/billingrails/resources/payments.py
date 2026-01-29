# This file is auto-generated. Do not edit manually.

from typing import Dict, Any

from ..types import (
    PaymentInput,
)


class PaymentsResource:
    """Payments resource"""

    def __init__(self, client):
        self.client = client

    def create(self, data: PaymentInput) -> Dict[str, Any]:
        """Create a payment
        
        Create an online or offline payment for an invoice, order, payment request, or credit grant."""
        return self.client.request("POST", f"/payments", json=data)
