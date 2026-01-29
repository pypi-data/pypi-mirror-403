# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .fee import Fee


class FeeListResponse(TypedDict, total=False):
    fees: Optional[List[Fee]]
    meta: Optional[dict]
