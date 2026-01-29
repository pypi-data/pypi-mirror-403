# This file is auto-generated. Do not edit manually.

from typing import TypedDict, Optional, List, Literal


class Error(TypedDict, total=False):
    """Field specific error details."""
    details: Optional[List[dict]]
    type: str
    code: Literal["internal_server_error", "too_many_requests", "method_not_allowed", "invalid_request_url", "unauthorized", "forbidden", "validation_error", "not_found"]
    message: str
