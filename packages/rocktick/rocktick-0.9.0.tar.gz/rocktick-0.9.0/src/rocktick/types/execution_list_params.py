# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ExecutionListParams"]


class ExecutionListParams(TypedDict, total=False):
    completed: Optional[bool]

    cron_id: Optional[str]

    cursor: Optional[str]

    from_: Annotated[Optional[int], PropertyInfo(alias="from")]

    limit: Optional[int]

    one_off_job_id: Optional[str]

    to: Optional[int]
