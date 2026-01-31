# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, TypedDict

from .http_request_param import HTTPRequestParam

__all__ = ["JobCreateParams"]


class JobCreateParams(TypedDict, total=False):
    execute_at: Required[int]

    request: Required[HTTPRequestParam]

    max_response_bytes: Optional[int]

    max_retries: Optional[int]

    region: Optional[str]

    timeout_ms: Optional[int]
