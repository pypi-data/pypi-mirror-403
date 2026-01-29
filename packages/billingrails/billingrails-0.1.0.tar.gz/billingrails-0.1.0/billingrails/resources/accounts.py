# This file is auto-generated. Do not edit manually.

from typing import Dict, Any

from ..types import (
    AccountBalancesResponse,
    AccountCreate,
    AccountDebit,
    AccountDebitResponse,
    AccountListResponse,
    AccountResponse,
    AccountUpdate,
)


class AccountsResource:
    """Accounts resource"""

    def __init__(self, client):
        self.client = client

    def retrieve(self, id: str, **params) -> AccountResponse:
        """Retrieve an account
        
        Retrieves an account by ID."""
        return self.client.request("GET", f"/accounts/{id}", params=params)

    def update(self, id: str, data: AccountUpdate) -> AccountResponse:
        """Update an account
        
        Updates an account."""
        return self.client.request("PUT", f"/accounts/{id}", json=data)

    def get_balances(self, id: str, **params) -> AccountBalancesResponse:
        """Get balances
        
        Retrieve credit balances for an account."""
        return self.client.request("GET", f"/accounts/{id}/balances", params=params)

    def debit(self, id: str, data: AccountDebit) -> AccountDebitResponse:
        """Debit balance
        
        Debits an account's balance."""
        return self.client.request("POST", f"/accounts/{id}/debit", json=data)

    def list(self, **params) -> AccountListResponse:
        """List accounts
        
        Retrieve a list of accounts."""
        return self.client.request("GET", f"/accounts", params=params)

    def create(self, data: AccountCreate) -> AccountResponse:
        """Create an account
        
        Creates an account."""
        return self.client.request("POST", f"/accounts", json=data)
