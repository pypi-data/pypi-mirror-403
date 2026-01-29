# This file is auto-generated. Do not edit manually.

from ..types import (
    SubscriptionCreate,
    SubscriptionListResponse,
    SubscriptionResponse,
)


class SubscriptionsResource:
    """Subscriptions resource"""

    def __init__(self, client):
        self.client = client

    def list(self, **params) -> SubscriptionListResponse:
        """List subscriptions
        
        Retrieves a list of subscriptions."""
        return self.client.request("GET", f"/biller/subscriptions", params=params)

    def create(self, data: SubscriptionCreate) -> SubscriptionResponse:
        """Create a subscription
        
        Creates a subscription."""
        return self.client.request("POST", f"/biller/subscriptions", json=data)

    def retrieve(self, id: str, **params) -> SubscriptionResponse:
        """Retrieve subscription
        
        Retrieves a subscription by ID."""
        return self.client.request("GET", f"/biller/subscriptions/{id}", params=params)

    def update(self, id: str, data: SubscriptionCreate) -> SubscriptionResponse:
        """Update a subscription
        
        Updates a subscription."""
        return self.client.request("PUT", f"/biller/subscriptions/{id}", json=data)
