# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, Mapping, cast
from typing_extensions import Self, Literal, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import RocktickError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import cron, jobs, verify, tenants, executions
    from .resources.cron import CronResource, AsyncCronResource
    from .resources.jobs import JobsResource, AsyncJobsResource
    from .resources.verify import VerifyResource, AsyncVerifyResource
    from .resources.tenants import TenantsResource, AsyncTenantsResource
    from .resources.executions import ExecutionsResource, AsyncExecutionsResource

__all__ = [
    "ENVIRONMENTS",
    "Timeout",
    "Transport",
    "ProxiesTypes",
    "RequestOptions",
    "Rocktick",
    "AsyncRocktick",
    "Client",
    "AsyncClient",
]

ENVIRONMENTS: Dict[str, str] = {
    "production": "https://cloud.rocktick.com",
    "local": "http://localhost:9090",
}


class Rocktick(SyncAPIClient):
    # client options
    api_key: str
    tenant_id: str | None

    _environment: Literal["production", "local"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        tenant_id: str | None = None,
        environment: Literal["production", "local"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Rocktick client instance.

        This automatically infers the `api_key` argument from the `ROCKTICK_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("ROCKTICK_API_KEY")
        if api_key is None:
            raise RocktickError(
                "The api_key client option must be set either by passing api_key to the client or by setting the ROCKTICK_API_KEY environment variable"
            )
        self.api_key = api_key

        self.tenant_id = tenant_id

        self._environment = environment

        base_url_env = os.environ.get("ROCKTICK_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `ROCKTICK_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def cron(self) -> CronResource:
        from .resources.cron import CronResource

        return CronResource(self)

    @cached_property
    def executions(self) -> ExecutionsResource:
        from .resources.executions import ExecutionsResource

        return ExecutionsResource(self)

    @cached_property
    def jobs(self) -> JobsResource:
        from .resources.jobs import JobsResource

        return JobsResource(self)

    @cached_property
    def tenants(self) -> TenantsResource:
        from .resources.tenants import TenantsResource

        return TenantsResource(self)

    @cached_property
    def verify(self) -> VerifyResource:
        from .resources.verify import VerifyResource

        return VerifyResource(self)

    @cached_property
    def with_raw_response(self) -> RocktickWithRawResponse:
        return RocktickWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RocktickWithStreamedResponse:
        return RocktickWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            "Tenant-Id": self.tenant_id if self.tenant_id is not None else Omit(),
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        tenant_id: str | None = None,
        environment: Literal["production", "local"] | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            tenant_id=tenant_id or self.tenant_id,
            base_url=base_url or self.base_url,
            environment=environment or self._environment,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncRocktick(AsyncAPIClient):
    # client options
    api_key: str
    tenant_id: str | None

    _environment: Literal["production", "local"] | NotGiven

    def __init__(
        self,
        *,
        api_key: str | None = None,
        tenant_id: str | None = None,
        environment: Literal["production", "local"] | NotGiven = not_given,
        base_url: str | httpx.URL | None | NotGiven = not_given,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncRocktick client instance.

        This automatically infers the `api_key` argument from the `ROCKTICK_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("ROCKTICK_API_KEY")
        if api_key is None:
            raise RocktickError(
                "The api_key client option must be set either by passing api_key to the client or by setting the ROCKTICK_API_KEY environment variable"
            )
        self.api_key = api_key

        self.tenant_id = tenant_id

        self._environment = environment

        base_url_env = os.environ.get("ROCKTICK_BASE_URL")
        if is_given(base_url) and base_url is not None:
            # cast required because mypy doesn't understand the type narrowing
            base_url = cast("str | httpx.URL", base_url)  # pyright: ignore[reportUnnecessaryCast]
        elif is_given(environment):
            if base_url_env and base_url is not None:
                raise ValueError(
                    "Ambiguous URL; The `ROCKTICK_BASE_URL` env var and the `environment` argument are given. If you want to use the environment, you must pass base_url=None",
                )

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc
        elif base_url_env is not None:
            base_url = base_url_env
        else:
            self._environment = environment = "production"

            try:
                base_url = ENVIRONMENTS[environment]
            except KeyError as exc:
                raise ValueError(f"Unknown environment: {environment}") from exc

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def cron(self) -> AsyncCronResource:
        from .resources.cron import AsyncCronResource

        return AsyncCronResource(self)

    @cached_property
    def executions(self) -> AsyncExecutionsResource:
        from .resources.executions import AsyncExecutionsResource

        return AsyncExecutionsResource(self)

    @cached_property
    def jobs(self) -> AsyncJobsResource:
        from .resources.jobs import AsyncJobsResource

        return AsyncJobsResource(self)

    @cached_property
    def tenants(self) -> AsyncTenantsResource:
        from .resources.tenants import AsyncTenantsResource

        return AsyncTenantsResource(self)

    @cached_property
    def verify(self) -> AsyncVerifyResource:
        from .resources.verify import AsyncVerifyResource

        return AsyncVerifyResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncRocktickWithRawResponse:
        return AsyncRocktickWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRocktickWithStreamedResponse:
        return AsyncRocktickWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            "Tenant-Id": self.tenant_id if self.tenant_id is not None else Omit(),
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        tenant_id: str | None = None,
        environment: Literal["production", "local"] | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            tenant_id=tenant_id or self.tenant_id,
            base_url=base_url or self.base_url,
            environment=environment or self._environment,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class RocktickWithRawResponse:
    _client: Rocktick

    def __init__(self, client: Rocktick) -> None:
        self._client = client

    @cached_property
    def cron(self) -> cron.CronResourceWithRawResponse:
        from .resources.cron import CronResourceWithRawResponse

        return CronResourceWithRawResponse(self._client.cron)

    @cached_property
    def executions(self) -> executions.ExecutionsResourceWithRawResponse:
        from .resources.executions import ExecutionsResourceWithRawResponse

        return ExecutionsResourceWithRawResponse(self._client.executions)

    @cached_property
    def jobs(self) -> jobs.JobsResourceWithRawResponse:
        from .resources.jobs import JobsResourceWithRawResponse

        return JobsResourceWithRawResponse(self._client.jobs)

    @cached_property
    def tenants(self) -> tenants.TenantsResourceWithRawResponse:
        from .resources.tenants import TenantsResourceWithRawResponse

        return TenantsResourceWithRawResponse(self._client.tenants)

    @cached_property
    def verify(self) -> verify.VerifyResourceWithRawResponse:
        from .resources.verify import VerifyResourceWithRawResponse

        return VerifyResourceWithRawResponse(self._client.verify)


class AsyncRocktickWithRawResponse:
    _client: AsyncRocktick

    def __init__(self, client: AsyncRocktick) -> None:
        self._client = client

    @cached_property
    def cron(self) -> cron.AsyncCronResourceWithRawResponse:
        from .resources.cron import AsyncCronResourceWithRawResponse

        return AsyncCronResourceWithRawResponse(self._client.cron)

    @cached_property
    def executions(self) -> executions.AsyncExecutionsResourceWithRawResponse:
        from .resources.executions import AsyncExecutionsResourceWithRawResponse

        return AsyncExecutionsResourceWithRawResponse(self._client.executions)

    @cached_property
    def jobs(self) -> jobs.AsyncJobsResourceWithRawResponse:
        from .resources.jobs import AsyncJobsResourceWithRawResponse

        return AsyncJobsResourceWithRawResponse(self._client.jobs)

    @cached_property
    def tenants(self) -> tenants.AsyncTenantsResourceWithRawResponse:
        from .resources.tenants import AsyncTenantsResourceWithRawResponse

        return AsyncTenantsResourceWithRawResponse(self._client.tenants)

    @cached_property
    def verify(self) -> verify.AsyncVerifyResourceWithRawResponse:
        from .resources.verify import AsyncVerifyResourceWithRawResponse

        return AsyncVerifyResourceWithRawResponse(self._client.verify)


class RocktickWithStreamedResponse:
    _client: Rocktick

    def __init__(self, client: Rocktick) -> None:
        self._client = client

    @cached_property
    def cron(self) -> cron.CronResourceWithStreamingResponse:
        from .resources.cron import CronResourceWithStreamingResponse

        return CronResourceWithStreamingResponse(self._client.cron)

    @cached_property
    def executions(self) -> executions.ExecutionsResourceWithStreamingResponse:
        from .resources.executions import ExecutionsResourceWithStreamingResponse

        return ExecutionsResourceWithStreamingResponse(self._client.executions)

    @cached_property
    def jobs(self) -> jobs.JobsResourceWithStreamingResponse:
        from .resources.jobs import JobsResourceWithStreamingResponse

        return JobsResourceWithStreamingResponse(self._client.jobs)

    @cached_property
    def tenants(self) -> tenants.TenantsResourceWithStreamingResponse:
        from .resources.tenants import TenantsResourceWithStreamingResponse

        return TenantsResourceWithStreamingResponse(self._client.tenants)

    @cached_property
    def verify(self) -> verify.VerifyResourceWithStreamingResponse:
        from .resources.verify import VerifyResourceWithStreamingResponse

        return VerifyResourceWithStreamingResponse(self._client.verify)


class AsyncRocktickWithStreamedResponse:
    _client: AsyncRocktick

    def __init__(self, client: AsyncRocktick) -> None:
        self._client = client

    @cached_property
    def cron(self) -> cron.AsyncCronResourceWithStreamingResponse:
        from .resources.cron import AsyncCronResourceWithStreamingResponse

        return AsyncCronResourceWithStreamingResponse(self._client.cron)

    @cached_property
    def executions(self) -> executions.AsyncExecutionsResourceWithStreamingResponse:
        from .resources.executions import AsyncExecutionsResourceWithStreamingResponse

        return AsyncExecutionsResourceWithStreamingResponse(self._client.executions)

    @cached_property
    def jobs(self) -> jobs.AsyncJobsResourceWithStreamingResponse:
        from .resources.jobs import AsyncJobsResourceWithStreamingResponse

        return AsyncJobsResourceWithStreamingResponse(self._client.jobs)

    @cached_property
    def tenants(self) -> tenants.AsyncTenantsResourceWithStreamingResponse:
        from .resources.tenants import AsyncTenantsResourceWithStreamingResponse

        return AsyncTenantsResourceWithStreamingResponse(self._client.tenants)

    @cached_property
    def verify(self) -> verify.AsyncVerifyResourceWithStreamingResponse:
        from .resources.verify import AsyncVerifyResourceWithStreamingResponse

        return AsyncVerifyResourceWithStreamingResponse(self._client.verify)


Client = Rocktick

AsyncClient = AsyncRocktick
