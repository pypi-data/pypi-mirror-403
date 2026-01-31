# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["VerifyRetrieveResponse"]


class VerifyRetrieveResponse(BaseModel):
    verified: bool

    hash: Optional[str] = None
    """The hex digest of the request body, or null if there isn't one for the request."""
