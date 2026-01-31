# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

from .http_request_param import HTTPRequestParam

__all__ = ["JobUpdateParams"]


class JobUpdateParams(TypedDict, total=False):
    execute_at: Optional[int]

    max_response_bytes: Optional[int]

    max_retries: Optional[int]

    region: Optional[str]

    request: Optional[HTTPRequestParam]

    timeout_ms: Optional[int]
