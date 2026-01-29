# This file is auto-generated. Do not edit manually.

from typing import Dict, Any

from ..types import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceResponse,
    InvoiceUpdate,
)


class InvoicesResource:
    """Invoices resource"""

    def __init__(self, client):
        self.client = client

    def issue(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Issue an invoice
        
        Issues an invoice."""
        return self.client.request("POST", f"/invoices/{id}/issue", json=data)

    def retrieve(self, id: str, **params) -> InvoiceResponse:
        """Retrieve invoice
        
        Retrieves an invoice by ID."""
        return self.client.request("GET", f"/invoices/{id}", params=params)

    def update(self, id: str, data: InvoiceUpdate) -> InvoiceResponse:
        """Update an invoice
        
        Updates an invoice."""
        return self.client.request("PUT", f"/invoices/{id}", json=data)

    def list(self, **params) -> InvoiceListResponse:
        """List invoices
        
        Retrieves a list of invoices."""
        return self.client.request("GET", f"/invoices", params=params)

    def create(self, data: InvoiceCreate) -> InvoiceResponse:
        """Create an invoice
        
        Creates an invoice."""
        return self.client.request("POST", f"/invoices", json=data)
