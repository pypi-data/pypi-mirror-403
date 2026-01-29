# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .credit_grant import CreditGrant


class CreditGrantListResponse(TypedDict, total=False):
    credit_grants: Optional[List[CreditGrant]]
    meta: Optional[dict]
