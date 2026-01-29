# This file is auto-generated. Do not edit manually.

from ..types import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)


class ProductsResource:
    """Products resource"""

    def __init__(self, client):
        self.client = client

    def list(self, **params) -> ProductListResponse:
        """List products
        
        Retrieves a list of products."""
        return self.client.request("GET", f"/seller/products", params=params)

    def create(self, data: ProductCreate) -> ProductResponse:
        """Create a product
        
        Creates a product."""
        return self.client.request("POST", f"/seller/products", json=data)

    def retrieve(self, id: str, **params) -> ProductResponse:
        """Retrieve a product
        
        Retrieves a product by ID."""
        return self.client.request("GET", f"/seller/products/{id}", params=params)

    def update(self, id: str, data: ProductUpdate) -> ProductResponse:
        """Update a product
        
        Updates a product."""
        return self.client.request("PUT", f"/seller/products/{id}", json=data)
