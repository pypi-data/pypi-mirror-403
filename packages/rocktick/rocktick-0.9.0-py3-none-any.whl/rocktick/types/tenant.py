# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["Tenant"]


class Tenant(BaseModel):
    id: str

    default_retries: int

    max_max_response_bytes: int

    max_request_bytes: int

    max_timeout: int

    max_tokens: int

    tok_per_day: int

    tokens: int
