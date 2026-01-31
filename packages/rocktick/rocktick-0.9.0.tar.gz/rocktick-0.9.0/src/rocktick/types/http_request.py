# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from .._models import BaseModel

__all__ = ["HTTPRequest"]


class HTTPRequest(BaseModel):
    headers: Dict[str, str]

    method: str

    url: str

    body: Optional[str] = None
