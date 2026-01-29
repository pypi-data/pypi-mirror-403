# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .plan import Plan


class PlanListResponse(TypedDict, total=False):
    meta: Optional[dict]
    plans: Optional[List[Plan]]
