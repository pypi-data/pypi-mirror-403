# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from rocktick import Rocktick, AsyncRocktick
from tests.utils import assert_matches_type
from rocktick.types import (
    CronJob,
    CronListResponse,
)
from rocktick.pagination import SyncCursorPage, AsyncCursorPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCron:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Rocktick) -> None:
        cron = client.cron.create(
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
            schedule="schedule",
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Rocktick) -> None:
        cron = client.cron.create(
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
                "body": "body",
            },
            schedule="schedule",
            max_response_bytes=0,
            max_retries=0,
            region="region",
            timeout_ms=0,
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Rocktick) -> None:
        response = client.cron.with_raw_response.create(
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
            schedule="schedule",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cron = response.parse()
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Rocktick) -> None:
        with client.cron.with_streaming_response.create(
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
            schedule="schedule",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cron = response.parse()
            assert_matches_type(CronJob, cron, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Rocktick) -> None:
        cron = client.cron.retrieve(
            "job_id",
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Rocktick) -> None:
        response = client.cron.with_raw_response.retrieve(
            "job_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cron = response.parse()
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Rocktick) -> None:
        with client.cron.with_streaming_response.retrieve(
            "job_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cron = response.parse()
            assert_matches_type(CronJob, cron, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Rocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            client.cron.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Rocktick) -> None:
        cron = client.cron.update(
            job_id="job_id",
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Rocktick) -> None:
        cron = client.cron.update(
            job_id="job_id",
            max_response_bytes=0,
            max_retries=0,
            region="region",
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
                "body": "body",
            },
            schedule="schedule",
            timeout_ms=0,
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Rocktick) -> None:
        response = client.cron.with_raw_response.update(
            job_id="job_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cron = response.parse()
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Rocktick) -> None:
        with client.cron.with_streaming_response.update(
            job_id="job_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cron = response.parse()
            assert_matches_type(CronJob, cron, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Rocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            client.cron.with_raw_response.update(
                job_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Rocktick) -> None:
        cron = client.cron.list()
        assert_matches_type(SyncCursorPage[CronListResponse], cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Rocktick) -> None:
        cron = client.cron.list(
            cursor="cursor",
            limit=0,
        )
        assert_matches_type(SyncCursorPage[CronListResponse], cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Rocktick) -> None:
        response = client.cron.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cron = response.parse()
        assert_matches_type(SyncCursorPage[CronListResponse], cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Rocktick) -> None:
        with client.cron.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cron = response.parse()
            assert_matches_type(SyncCursorPage[CronListResponse], cron, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCron:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncRocktick) -> None:
        cron = await async_client.cron.create(
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
            schedule="schedule",
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncRocktick) -> None:
        cron = await async_client.cron.create(
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
                "body": "body",
            },
            schedule="schedule",
            max_response_bytes=0,
            max_retries=0,
            region="region",
            timeout_ms=0,
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncRocktick) -> None:
        response = await async_client.cron.with_raw_response.create(
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
            schedule="schedule",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cron = await response.parse()
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncRocktick) -> None:
        async with async_client.cron.with_streaming_response.create(
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
            },
            schedule="schedule",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cron = await response.parse()
            assert_matches_type(CronJob, cron, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncRocktick) -> None:
        cron = await async_client.cron.retrieve(
            "job_id",
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncRocktick) -> None:
        response = await async_client.cron.with_raw_response.retrieve(
            "job_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cron = await response.parse()
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncRocktick) -> None:
        async with async_client.cron.with_streaming_response.retrieve(
            "job_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cron = await response.parse()
            assert_matches_type(CronJob, cron, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncRocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            await async_client.cron.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncRocktick) -> None:
        cron = await async_client.cron.update(
            job_id="job_id",
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncRocktick) -> None:
        cron = await async_client.cron.update(
            job_id="job_id",
            max_response_bytes=0,
            max_retries=0,
            region="region",
            request={
                "headers": {"foo": "string"},
                "method": "method",
                "url": "url",
                "body": "body",
            },
            schedule="schedule",
            timeout_ms=0,
        )
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncRocktick) -> None:
        response = await async_client.cron.with_raw_response.update(
            job_id="job_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cron = await response.parse()
        assert_matches_type(CronJob, cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncRocktick) -> None:
        async with async_client.cron.with_streaming_response.update(
            job_id="job_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cron = await response.parse()
            assert_matches_type(CronJob, cron, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncRocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            await async_client.cron.with_raw_response.update(
                job_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncRocktick) -> None:
        cron = await async_client.cron.list()
        assert_matches_type(AsyncCursorPage[CronListResponse], cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncRocktick) -> None:
        cron = await async_client.cron.list(
            cursor="cursor",
            limit=0,
        )
        assert_matches_type(AsyncCursorPage[CronListResponse], cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncRocktick) -> None:
        response = await async_client.cron.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cron = await response.parse()
        assert_matches_type(AsyncCursorPage[CronListResponse], cron, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncRocktick) -> None:
        async with async_client.cron.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cron = await response.parse()
            assert_matches_type(AsyncCursorPage[CronListResponse], cron, path=["response"])

        assert cast(Any, response.is_closed) is True
