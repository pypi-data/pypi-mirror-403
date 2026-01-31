# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, TypedDict

__all__ = ["HTTPRequestParam"]


class HTTPRequestParam(TypedDict, total=False):
    headers: Required[Dict[str, str]]

    method: Required[str]

    url: Required[str]

    body: Optional[str]
