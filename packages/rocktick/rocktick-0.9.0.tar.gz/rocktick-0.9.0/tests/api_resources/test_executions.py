# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from rocktick import Rocktick, AsyncRocktick
from tests.utils import assert_matches_type
from rocktick.types import Execution, ExecutionListResponse
from rocktick.pagination import SyncCursorPage, AsyncCursorPage

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestExecutions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Rocktick) -> None:
        execution = client.executions.retrieve(
            "execution_id",
        )
        assert_matches_type(Execution, execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Rocktick) -> None:
        response = client.executions.with_raw_response.retrieve(
            "execution_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execution = response.parse()
        assert_matches_type(Execution, execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Rocktick) -> None:
        with client.executions.with_streaming_response.retrieve(
            "execution_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execution = response.parse()
            assert_matches_type(Execution, execution, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Rocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `execution_id` but received ''"):
            client.executions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Rocktick) -> None:
        execution = client.executions.list()
        assert_matches_type(SyncCursorPage[ExecutionListResponse], execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Rocktick) -> None:
        execution = client.executions.list(
            completed=True,
            cron_id="cron_id",
            cursor="cursor",
            from_=0,
            limit=0,
            one_off_job_id="one_off_job_id",
            to=0,
        )
        assert_matches_type(SyncCursorPage[ExecutionListResponse], execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Rocktick) -> None:
        response = client.executions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execution = response.parse()
        assert_matches_type(SyncCursorPage[ExecutionListResponse], execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Rocktick) -> None:
        with client.executions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execution = response.parse()
            assert_matches_type(SyncCursorPage[ExecutionListResponse], execution, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncExecutions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncRocktick) -> None:
        execution = await async_client.executions.retrieve(
            "execution_id",
        )
        assert_matches_type(Execution, execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncRocktick) -> None:
        response = await async_client.executions.with_raw_response.retrieve(
            "execution_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execution = await response.parse()
        assert_matches_type(Execution, execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncRocktick) -> None:
        async with async_client.executions.with_streaming_response.retrieve(
            "execution_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execution = await response.parse()
            assert_matches_type(Execution, execution, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncRocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `execution_id` but received ''"):
            await async_client.executions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncRocktick) -> None:
        execution = await async_client.executions.list()
        assert_matches_type(AsyncCursorPage[ExecutionListResponse], execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncRocktick) -> None:
        execution = await async_client.executions.list(
            completed=True,
            cron_id="cron_id",
            cursor="cursor",
            from_=0,
            limit=0,
            one_off_job_id="one_off_job_id",
            to=0,
        )
        assert_matches_type(AsyncCursorPage[ExecutionListResponse], execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncRocktick) -> None:
        response = await async_client.executions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        execution = await response.parse()
        assert_matches_type(AsyncCursorPage[ExecutionListResponse], execution, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncRocktick) -> None:
        async with async_client.executions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            execution = await response.parse()
            assert_matches_type(AsyncCursorPage[ExecutionListResponse], execution, path=["response"])

        assert cast(Any, response.is_closed) is True
