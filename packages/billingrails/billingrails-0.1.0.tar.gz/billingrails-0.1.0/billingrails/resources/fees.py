# This file is auto-generated. Do not edit manually.

from typing import Dict, Any

from ..types import (
    FeeCreate,
    FeeListResponse,
    FeeResponse,
    FeeUpdate,
)


class FeesResource:
    """Fees resource"""

    def __init__(self, client):
        self.client = client

    def retrieve(self, id: str, **params) -> FeeResponse:
        """Retrieve fee
        
        Retrieves a fee by ID."""
        return self.client.request("GET", f"/biller/fees/{id}", params=params)

    def update(self, id: str, data: FeeUpdate) -> FeeResponse:
        """Update a fee
        
        Updates a fee."""
        return self.client.request("PUT", f"/biller/fees/{id}", json=data)

    def delete(self, id: str) -> Dict[str, Any]:
        """Delete a fee
        
        Deletes a fee."""
        return self.client.request("DELETE", f"/biller/fees/{id}")

    def list(self) -> FeeListResponse:
        """List fees
        
        Retrieve a list of fees."""
        return self.client.request("GET", f"/biller/fees")

    def create(self, data: FeeCreate) -> FeeResponse:
        """Create a fee
        
        Creates a fee."""
        return self.client.request("POST", f"/biller/fees", json=data)
