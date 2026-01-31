# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from .._models import BaseModel
from .execution import Execution
from .http_request import HTTPRequest

__all__ = ["CronJob"]


class CronJob(BaseModel):
    id: str

    executions: List[Execution]

    max_retries: int

    region: str

    request: HTTPRequest

    schedule: str

    max_response_bytes: Optional[int] = None

    tenant_id: Optional[str] = None

    timeout_ms: Optional[int] = None
