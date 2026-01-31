# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from rocktick import Rocktick, AsyncRocktick
from tests.utils import assert_matches_type
from rocktick.types import (
    OneOffJob,
    JobListResponse,
)
from rocktick.pagination import SyncCursorPage, AsyncCursorPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestJobs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Rocktick) -> None:
        job = client.jobs.create(
            execute_at=0,
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Rocktick) -> None:
        job = client.jobs.create(
            execute_at=0,
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
                "body": "body",
            },
            max_response_bytes=0,
            max_retries=0,
            region="region",
            timeout_ms=0,
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Rocktick) -> None:
        response = client.jobs.with_raw_response.create(
            execute_at=0,
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Rocktick) -> None:
        with client.jobs.with_streaming_response.create(
            execute_at=0,
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(OneOffJob, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Rocktick) -> None:
        job = client.jobs.retrieve(
            "job_id",
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Rocktick) -> None:
        response = client.jobs.with_raw_response.retrieve(
            "job_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Rocktick) -> None:
        with client.jobs.with_streaming_response.retrieve(
            "job_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(OneOffJob, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Rocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            client.jobs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Rocktick) -> None:
        job = client.jobs.update(
            job_id="job_id",
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Rocktick) -> None:
        job = client.jobs.update(
            job_id="job_id",
            execute_at=0,
            max_response_bytes=0,
            max_retries=0,
            region="region",
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
                "body": "body",
            },
            timeout_ms=0,
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Rocktick) -> None:
        response = client.jobs.with_raw_response.update(
            job_id="job_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Rocktick) -> None:
        with client.jobs.with_streaming_response.update(
            job_id="job_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(OneOffJob, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Rocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            client.jobs.with_raw_response.update(
                job_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Rocktick) -> None:
        job = client.jobs.list()
        assert_matches_type(SyncCursorPage[JobListResponse], job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Rocktick) -> None:
        job = client.jobs.list(
            cursor="cursor",
            limit=0,
        )
        assert_matches_type(SyncCursorPage[JobListResponse], job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Rocktick) -> None:
        response = client.jobs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(SyncCursorPage[JobListResponse], job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Rocktick) -> None:
        with client.jobs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(SyncCursorPage[JobListResponse], job, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncJobs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncRocktick) -> None:
        job = await async_client.jobs.create(
            execute_at=0,
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncRocktick) -> None:
        job = await async_client.jobs.create(
            execute_at=0,
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
                "body": "body",
            },
            max_response_bytes=0,
            max_retries=0,
            region="region",
            timeout_ms=0,
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncRocktick) -> None:
        response = await async_client.jobs.with_raw_response.create(
            execute_at=0,
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncRocktick) -> None:
        async with async_client.jobs.with_streaming_response.create(
            execute_at=0,
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(OneOffJob, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncRocktick) -> None:
        job = await async_client.jobs.retrieve(
            "job_id",
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncRocktick) -> None:
        response = await async_client.jobs.with_raw_response.retrieve(
            "job_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncRocktick) -> None:
        async with async_client.jobs.with_streaming_response.retrieve(
            "job_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(OneOffJob, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncRocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            await async_client.jobs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncRocktick) -> None:
        job = await async_client.jobs.update(
            job_id="job_id",
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncRocktick) -> None:
        job = await async_client.jobs.update(
            job_id="job_id",
            execute_at=0,
            max_response_bytes=0,
            max_retries=0,
            region="region",
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
                "body": "body",
            },
            timeout_ms=0,
        )
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncRocktick) -> None:
        response = await async_client.jobs.with_raw_response.update(
            job_id="job_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(OneOffJob, job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncRocktick) -> None:
        async with async_client.jobs.with_streaming_response.update(
            job_id="job_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(OneOffJob, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncRocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            await async_client.jobs.with_raw_response.update(
                job_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncRocktick) -> None:
        job = await async_client.jobs.list()
        assert_matches_type(AsyncCursorPage[JobListResponse], job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncRocktick) -> None:
        job = await async_client.jobs.list(
            cursor="cursor",
            limit=0,
        )
        assert_matches_type(AsyncCursorPage[JobListResponse], job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncRocktick) -> None:
        response = await async_client.jobs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(AsyncCursorPage[JobListResponse], job, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncRocktick) -> None:
        async with async_client.jobs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(AsyncCursorPage[JobListResponse], job, path=["response"])

        assert cast(Any, response.is_closed) is True
