# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import cron_list_params, cron_create_params, cron_update_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncCursorPage, AsyncCursorPage
from .._base_client import AsyncPaginator, make_request_options
from ..types.cron_job import CronJob
from ..types.cron_list_response import CronListResponse
from ..types.http_request_param import HTTPRequestParam

__all__ = ["CronResource", "AsyncCronResource"]


class CronResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CronResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/violetbuse/rocktick-python#accessing-raw-response-data-eg-headers
        """
        return CronResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CronResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/violetbuse/rocktick-python#with_streaming_response
        """
        return CronResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        request: HTTPRequestParam,
        schedule: str,
        max_response_bytes: Optional[int] | Omit = omit,
        max_retries: Optional[int] | Omit = omit,
        region: Optional[str] | Omit = omit,
        timeout_ms: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CronJob:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/cron",
            body=maybe_transform(
                {
                    "request": request,
                    "schedule": schedule,
                    "max_response_bytes": max_response_bytes,
                    "max_retries": max_retries,
                    "region": region,
                    "timeout_ms": timeout_ms,
                },
                cron_create_params.CronCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CronJob,
        )

    def retrieve(
        self,
        job_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CronJob:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not job_id:
            raise ValueError(f"Expected a non-empty value for `job_id` but received {job_id!r}")
        return self._get(
            f"/api/cron/{job_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CronJob,
        )

    def update(
        self,
        job_id: str,
        *,
        max_response_bytes: Optional[int] | Omit = omit,
        max_retries: Optional[int] | Omit = omit,
        region: Optional[str] | Omit = omit,
        request: Optional[HTTPRequestParam] | Omit = omit,
        schedule: Optional[str] | Omit = omit,
        timeout_ms: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CronJob:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not job_id:
            raise ValueError(f"Expected a non-empty value for `job_id` but received {job_id!r}")
        return self._post(
            f"/api/cron/{job_id}",
            body=maybe_transform(
                {
                    "max_response_bytes": max_response_bytes,
                    "max_retries": max_retries,
                    "region": region,
                    "request": request,
                    "schedule": schedule,
                    "timeout_ms": timeout_ms,
                },
                cron_update_params.CronUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CronJob,
        )

    def list(
        self,
        *,
        cursor: Optional[str] | Omit = omit,
        limit: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursorPage[CronListResponse]:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/cron",
            page=SyncCursorPage[CronListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                    },
                    cron_list_params.CronListParams,
                ),
            ),
            model=CronListResponse,
        )


class AsyncCronResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCronResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/violetbuse/rocktick-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCronResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCronResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/violetbuse/rocktick-python#with_streaming_response
        """
        return AsyncCronResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        request: HTTPRequestParam,
        schedule: str,
        max_response_bytes: Optional[int] | Omit = omit,
        max_retries: Optional[int] | Omit = omit,
        region: Optional[str] | Omit = omit,
        timeout_ms: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CronJob:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/cron",
            body=await async_maybe_transform(
                {
                    "request": request,
                    "schedule": schedule,
                    "max_response_bytes": max_response_bytes,
                    "max_retries": max_retries,
                    "region": region,
                    "timeout_ms": timeout_ms,
                },
                cron_create_params.CronCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CronJob,
        )

    async def retrieve(
        self,
        job_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CronJob:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not job_id:
            raise ValueError(f"Expected a non-empty value for `job_id` but received {job_id!r}")
        return await self._get(
            f"/api/cron/{job_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CronJob,
        )

    async def update(
        self,
        job_id: str,
        *,
        max_response_bytes: Optional[int] | Omit = omit,
        max_retries: Optional[int] | Omit = omit,
        region: Optional[str] | Omit = omit,
        request: Optional[HTTPRequestParam] | Omit = omit,
        schedule: Optional[str] | Omit = omit,
        timeout_ms: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CronJob:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not job_id:
            raise ValueError(f"Expected a non-empty value for `job_id` but received {job_id!r}")
        return await self._post(
            f"/api/cron/{job_id}",
            body=await async_maybe_transform(
                {
                    "max_response_bytes": max_response_bytes,
                    "max_retries": max_retries,
                    "region": region,
                    "request": request,
                    "schedule": schedule,
                    "timeout_ms": timeout_ms,
                },
                cron_update_params.CronUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CronJob,
        )

    def list(
        self,
        *,
        cursor: Optional[str] | Omit = omit,
        limit: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[CronListResponse, AsyncCursorPage[CronListResponse]]:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get_api_list(
            "/api/cron",
            page=AsyncCursorPage[CronListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "cursor": cursor,
                        "limit": limit,
                    },
                    cron_list_params.CronListParams,
                ),
            ),
            model=CronListResponse,
        )


class CronResourceWithRawResponse:
    def __init__(self, cron: CronResource) -> None:
        self._cron = cron

        self.create = to_raw_response_wrapper(
            cron.create,
        )
        self.retrieve = to_raw_response_wrapper(
            cron.retrieve,
        )
        self.update = to_raw_response_wrapper(
            cron.update,
        )
        self.list = to_raw_response_wrapper(
            cron.list,
        )


class AsyncCronResourceWithRawResponse:
    def __init__(self, cron: AsyncCronResource) -> None:
        self._cron = cron

        self.create = async_to_raw_response_wrapper(
            cron.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            cron.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            cron.update,
        )
        self.list = async_to_raw_response_wrapper(
            cron.list,
        )


class CronResourceWithStreamingResponse:
    def __init__(self, cron: CronResource) -> None:
        self._cron = cron

        self.create = to_streamed_response_wrapper(
            cron.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            cron.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            cron.update,
        )
        self.list = to_streamed_response_wrapper(
            cron.list,
        )


class AsyncCronResourceWithStreamingResponse:
    def __init__(self, cron: AsyncCronResource) -> None:
        self._cron = cron

        self.create = async_to_streamed_response_wrapper(
            cron.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            cron.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            cron.update,
        )
        self.list = async_to_streamed_response_wrapper(
            cron.list,
        )
