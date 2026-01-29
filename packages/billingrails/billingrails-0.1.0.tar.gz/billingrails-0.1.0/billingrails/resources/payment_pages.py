# This file is auto-generated. Do not edit manually.

from ..types import (
    PaymentPageCreate,
    PaymentPageListResponse,
    PaymentPageResponse,
    PaymentPageUpdate,
)


class PaymentPagesResource:
    """Payment pages resource"""

    def __init__(self, client):
        self.client = client

    def list(self, **params) -> PaymentPageListResponse:
        """List payment pages
        
        Retrieves a list of payment pages."""
        return self.client.request("GET", f"/payment_pages", params=params)

    def create(self, data: PaymentPageCreate) -> PaymentPageResponse:
        """Create payment page
        
        Creates a new payment page."""
        return self.client.request("POST", f"/payment_pages", json=data)

    def retrieve(self, id: str, **params) -> PaymentPageResponse:
        """Retrieve payment page
        
        Retrieves a payment page by ID."""
        return self.client.request("GET", f"/payment_pages/{id}", params=params)

    def update(self, id: str, data: PaymentPageUpdate) -> PaymentPageResponse:
        """Update payment page
        
        Updates a payment page."""
        return self.client.request("PUT", f"/payment_pages/{id}", json=data)
