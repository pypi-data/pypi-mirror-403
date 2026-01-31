# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["TenantUpdateParams"]


class TenantUpdateParams(TypedDict, total=False):
    default_retries: Optional[int]

    max_max_response_bytes: Optional[int]

    max_request_bytes: Optional[int]

    max_timeout: Optional[int]

    max_tokens: Optional[int]

    tok_per_day: Optional[int]

    tokens: Optional[int]
