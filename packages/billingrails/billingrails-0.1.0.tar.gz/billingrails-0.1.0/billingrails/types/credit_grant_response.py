# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional

from .credit_grant import CreditGrant


class CreditGrantResponse(TypedDict, total=False):
    meta: Optional[dict]
    credit_grant: Optional[CreditGrant]
