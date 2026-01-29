# This file is auto-generated. Do not edit manually.

from typing import Dict, Any

from ..types import (
    EventBatchInput,
    EventInput,
)


class EventsResource:
    """Events resource"""

    def __init__(self, client):
        self.client = client

    def ingest(self, data: EventInput) -> Dict[str, Any]:
        """Ingest event
        
        Ingests an event."""
        return self.client.request("POST", f"/biller/events/ingest", json=data)

    def ingest_batch(self, data: EventBatchInput) -> Dict[str, Any]:
        """Ingest batch events
        
        Ingests batch events."""
        return self.client.request("POST", f"/biller/events/batch", json=data)
