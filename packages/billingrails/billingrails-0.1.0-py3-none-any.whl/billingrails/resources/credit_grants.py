# This file is auto-generated. Do not edit manually.

from typing import Dict, Any

from ..types import (
    CreditGrantCreate,
    CreditGrantListResponse,
    CreditGrantResponse,
)


class CreditGrantsResource:
    """Credit grants resource"""

    def __init__(self, client):
        self.client = client

    def list(self) -> CreditGrantListResponse:
        """List credit grants
        
        Retrieves a list of credit grants."""
        return self.client.request("GET", f"/credit_grants")

    def create(self, data: CreditGrantCreate) -> CreditGrantResponse:
        """Create a credit grant
        
        Creates a credit grant."""
        return self.client.request("POST", f"/credit_grants", json=data)

    def retrieve(self, id: str, **params) -> CreditGrantResponse:
        """Retrieve a credit grant
        
        Retrieves a credit grant by ID."""
        return self.client.request("GET", f"/credit_grants/{id}", params=params)

    def reverse_transaction(self, id: str, data: Dict[str, Any]) -> CreditGrantResponse:
        """Reverse credit grant transaction
        
        Reverses a credit grant usage."""
        return self.client.request("POST", f"/credit_grants/{id}/reverse_transaction", json=data)

    def apply(self, id: str, data: Dict[str, Any]) -> CreditGrantResponse:
        """Apply credit grant
        
        Applies a credit grant to an invoice or logs an external usage."""
        return self.client.request("POST", f"/credit_grants/{id}/apply", json=data)

    def expire(self, id: str) -> CreditGrantResponse:
        """Expire credit grant
        
        Expires a credit grant."""
        return self.client.request("POST", f"/credit_grants/{id}/expire", json={})
