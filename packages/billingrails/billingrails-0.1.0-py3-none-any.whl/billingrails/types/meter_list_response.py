# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List

from .meter import Meter


class MeterListResponse(TypedDict, total=False):
    meta: Optional[dict]
    meters: Optional[List[Meter]]
