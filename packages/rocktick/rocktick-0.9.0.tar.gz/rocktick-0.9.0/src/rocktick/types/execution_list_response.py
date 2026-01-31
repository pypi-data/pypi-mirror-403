# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel
from .http_request import HTTPRequest
from .http_response import HTTPResponse

__all__ = ["ExecutionListResponse"]


class ExecutionListResponse(BaseModel):
    id: str

    max_retries: int

    region: str

    request: HTTPRequest

    scheduled_at: int

    cron_job_id: Optional[str] = None

    executed_at: Optional[int] = None

    max_response_bytes: Optional[int] = None

    one_off_job_id: Optional[str] = None

    response: Optional[HTTPResponse] = None

    response_error: Optional[str] = None

    retry_for: Optional[str] = None

    success: Optional[bool] = None

    tenant_id: Optional[str] = None

    timeout_ms: Optional[int] = None
