# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List


class ListResponseMeta(TypedDict):
    """Pagination metadata"""
    page: int
    page_size: int
    total_pages: int
    total_count: int


class ApiErrorDetails(TypedDict, total=False):
    """API error details"""
    field: Optional[str]
    message: Optional[str]


class ApiError(TypedDict):
    """API error response"""
    type: str
    code: str
    message: str
    details: Optional[List[ApiErrorDetails]]
