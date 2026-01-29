# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional

from .account import Account


class AccountResponse(TypedDict, total=False):
    meta: Optional[dict]
    account: Optional[Account]
