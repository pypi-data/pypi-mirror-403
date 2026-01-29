# This file is auto-generated. Do not edit manually.

from ..types import (
    PlanCreate,
    PlanListResponse,
    PlanResponse,
    PlanUpdate,
)


class PlansResource:
    """Plans resource"""

    def __init__(self, client):
        self.client = client

    def list(self, **params) -> PlanListResponse:
        """List plans
        
        Retrieves a list of plans."""
        return self.client.request("GET", f"/biller/plans", params=params)

    def create(self, data: PlanCreate) -> PlanResponse:
        """Create a plan
        
        Creates a plan."""
        return self.client.request("POST", f"/biller/plans", json=data)

    def retrieve(self, id: str, **params) -> PlanResponse:
        """Retrieve a plan
        
        Retrieves plan by ID."""
        return self.client.request("GET", f"/biller/plans/{id}", params=params)

    def update(self, id: str, data: PlanUpdate) -> PlanResponse:
        """Update a plan
        
        Updates a plan."""
        return self.client.request("PUT", f"/biller/plans/{id}", json=data)
