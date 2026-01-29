# This file is auto-generated. Do not edit manually.

from typing import Dict, Any

from ..types import (
    OrderCreate,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)


class OrdersResource:
    """Orders resource"""

    def __init__(self, client):
        self.client = client

    def list(self, **params) -> OrderListResponse:
        """List orders
        
        Retrieves a list of orders."""
        return self.client.request("GET", f"/seller/orders", params=params)

    def create(self, data: OrderCreate) -> OrderResponse:
        """Create an order
        
        Creates an order."""
        return self.client.request("POST", f"/seller/orders", json=data)

    def retrieve(self, id: str, **params) -> OrderResponse:
        """Retrieve an order
        
        Retrieves an order by ID."""
        return self.client.request("GET", f"/seller/orders/{id}", params=params)

    def update(self, id: str, data: OrderUpdate) -> OrderResponse:
        """Update an order
        
        Updates an order."""
        return self.client.request("PUT", f"/seller/orders/{id}", json=data)

    def cancel(self, id: str) -> Dict[str, Any]:
        """Cancel an order
        
        Cancels an order."""
        return self.client.request("POST", f"/seller/orders/{id}/cancel", json={})
