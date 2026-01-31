# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["TenantCreateParams"]


class TenantCreateParams(TypedDict, total=False):
    default_retries: Required[int]

    max_max_response_bytes: Required[int]

    max_request_bytes: Required[int]

    max_timeout: Required[int]

    max_tokens: Required[int]

    tok_per_day: Required[int]
