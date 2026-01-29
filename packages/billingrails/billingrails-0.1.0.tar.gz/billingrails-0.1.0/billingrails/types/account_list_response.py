# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .account import Account


class AccountListResponse(TypedDict, total=False):
    meta: Optional[dict]
    accounts: Optional[List[Account]]
