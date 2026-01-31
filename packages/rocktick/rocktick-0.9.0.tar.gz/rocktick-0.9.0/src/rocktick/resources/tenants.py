# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import tenant_create_params, tenant_update_params
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
from .._base_client import make_request_options
from ..types.tenant import Tenant

__all__ = ["TenantsResource", "AsyncTenantsResource"]


class TenantsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TenantsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/violetbuse/rocktick-python#accessing-raw-response-data-eg-headers
        """
        return TenantsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TenantsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/violetbuse/rocktick-python#with_streaming_response
        """
        return TenantsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        default_retries: int,
        max_max_response_bytes: int,
        max_request_bytes: int,
        max_timeout: int,
        max_tokens: int,
        tok_per_day: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Tenant:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/tenants",
            body=maybe_transform(
                {
                    "default_retries": default_retries,
                    "max_max_response_bytes": max_max_response_bytes,
                    "max_request_bytes": max_request_bytes,
                    "max_timeout": max_timeout,
                    "max_tokens": max_tokens,
                    "tok_per_day": tok_per_day,
                },
                tenant_create_params.TenantCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Tenant,
        )

    def retrieve(
        self,
        tenant_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Tenant:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tenant_id:
            raise ValueError(f"Expected a non-empty value for `tenant_id` but received {tenant_id!r}")
        return self._get(
            f"/api/tenants/{tenant_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Tenant,
        )

    def update(
        self,
        tenant_id: str,
        *,
        default_retries: Optional[int] | Omit = omit,
        max_max_response_bytes: Optional[int] | Omit = omit,
        max_request_bytes: Optional[int] | Omit = omit,
        max_timeout: Optional[int] | Omit = omit,
        max_tokens: Optional[int] | Omit = omit,
        tok_per_day: Optional[int] | Omit = omit,
        tokens: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Tenant:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tenant_id:
            raise ValueError(f"Expected a non-empty value for `tenant_id` but received {tenant_id!r}")
        return self._post(
            f"/api/tenants/{tenant_id}",
            body=maybe_transform(
                {
                    "default_retries": default_retries,
                    "max_max_response_bytes": max_max_response_bytes,
                    "max_request_bytes": max_request_bytes,
                    "max_timeout": max_timeout,
                    "max_tokens": max_tokens,
                    "tok_per_day": tok_per_day,
                    "tokens": tokens,
                },
                tenant_update_params.TenantUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Tenant,
        )


class AsyncTenantsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTenantsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/violetbuse/rocktick-python#accessing-raw-response-data-eg-headers
        """
        return AsyncTenantsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTenantsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/violetbuse/rocktick-python#with_streaming_response
        """
        return AsyncTenantsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        default_retries: int,
        max_max_response_bytes: int,
        max_request_bytes: int,
        max_timeout: int,
        max_tokens: int,
        tok_per_day: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Tenant:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/tenants",
            body=await async_maybe_transform(
                {
                    "default_retries": default_retries,
                    "max_max_response_bytes": max_max_response_bytes,
                    "max_request_bytes": max_request_bytes,
                    "max_timeout": max_timeout,
                    "max_tokens": max_tokens,
                    "tok_per_day": tok_per_day,
                },
                tenant_create_params.TenantCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Tenant,
        )

    async def retrieve(
        self,
        tenant_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Tenant:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tenant_id:
            raise ValueError(f"Expected a non-empty value for `tenant_id` but received {tenant_id!r}")
        return await self._get(
            f"/api/tenants/{tenant_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Tenant,
        )

    async def update(
        self,
        tenant_id: str,
        *,
        default_retries: Optional[int] | Omit = omit,
        max_max_response_bytes: Optional[int] | Omit = omit,
        max_request_bytes: Optional[int] | Omit = omit,
        max_timeout: Optional[int] | Omit = omit,
        max_tokens: Optional[int] | Omit = omit,
        tok_per_day: Optional[int] | Omit = omit,
        tokens: Optional[int] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Tenant:
        """
        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not tenant_id:
            raise ValueError(f"Expected a non-empty value for `tenant_id` but received {tenant_id!r}")
        return await self._post(
            f"/api/tenants/{tenant_id}",
            body=await async_maybe_transform(
                {
                    "default_retries": default_retries,
                    "max_max_response_bytes": max_max_response_bytes,
                    "max_request_bytes": max_request_bytes,
                    "max_timeout": max_timeout,
                    "max_tokens": max_tokens,
                    "tok_per_day": tok_per_day,
                    "tokens": tokens,
                },
                tenant_update_params.TenantUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Tenant,
        )


class TenantsResourceWithRawResponse:
    def __init__(self, tenants: TenantsResource) -> None:
        self._tenants = tenants

        self.create = to_raw_response_wrapper(
            tenants.create,
        )
        self.retrieve = to_raw_response_wrapper(
            tenants.retrieve,
        )
        self.update = to_raw_response_wrapper(
            tenants.update,
        )


class AsyncTenantsResourceWithRawResponse:
    def __init__(self, tenants: AsyncTenantsResource) -> None:
        self._tenants = tenants

        self.create = async_to_raw_response_wrapper(
            tenants.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            tenants.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            tenants.update,
        )


class TenantsResourceWithStreamingResponse:
    def __init__(self, tenants: TenantsResource) -> None:
        self._tenants = tenants

        self.create = to_streamed_response_wrapper(
            tenants.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            tenants.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            tenants.update,
        )


class AsyncTenantsResourceWithStreamingResponse:
    def __init__(self, tenants: AsyncTenantsResource) -> None:
        self._tenants = tenants

        self.create = async_to_streamed_response_wrapper(
            tenants.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            tenants.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            tenants.update,
        )
