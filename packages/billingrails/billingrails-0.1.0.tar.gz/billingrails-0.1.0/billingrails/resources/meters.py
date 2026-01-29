# This file is auto-generated. Do not edit manually.

from ..types import (
    MeterCreate,
    MeterListResponse,
    MeterResponse,
    MeterUpdate,
)


class MetersResource:
    """Meters resource"""

    def __init__(self, client):
        self.client = client

    def retrieve(self, id: str, **params) -> MeterResponse:
        """Retrieve a meter
        
        Retrieves meter by ID."""
        return self.client.request("GET", f"/biller/meters/{id}", params=params)

    def update(self, id: str, data: MeterUpdate) -> MeterResponse:
        """Update a meter
        
        Updates a meter."""
        return self.client.request("PUT", f"/biller/meters/{id}", json=data)

    def list(self, **params) -> MeterListResponse:
        """List meters
        
        Retrieves a list of meters."""
        return self.client.request("GET", f"/biller/meters", params=params)

    def create(self, data: MeterCreate) -> MeterResponse:
        """Create a meter
        
        Creates a meter."""
        return self.client.request("POST", f"/biller/meters", json=data)
