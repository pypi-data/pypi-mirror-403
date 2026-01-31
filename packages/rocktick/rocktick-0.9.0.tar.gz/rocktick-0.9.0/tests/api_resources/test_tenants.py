# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from rocktick import Rocktick, AsyncRocktick
from tests.utils import assert_matches_type
from rocktick.types import Tenant

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTenants:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Rocktick) -> None:
        tenant = client.tenants.create(
            default_retries=0,
            max_max_response_bytes=0,
            max_request_bytes=0,
            max_timeout=0,
            max_tokens=0,
            tok_per_day=0,
        )
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Rocktick) -> None:
        response = client.tenants.with_raw_response.create(
            default_retries=0,
            max_max_response_bytes=0,
            max_request_bytes=0,
            max_timeout=0,
            max_tokens=0,
            tok_per_day=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tenant = response.parse()
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Rocktick) -> None:
        with client.tenants.with_streaming_response.create(
            default_retries=0,
            max_max_response_bytes=0,
            max_request_bytes=0,
            max_timeout=0,
            max_tokens=0,
            tok_per_day=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tenant = response.parse()
            assert_matches_type(Tenant, tenant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Rocktick) -> None:
        tenant = client.tenants.retrieve(
            "tenant_id",
        )
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Rocktick) -> None:
        response = client.tenants.with_raw_response.retrieve(
            "tenant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tenant = response.parse()
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Rocktick) -> None:
        with client.tenants.with_streaming_response.retrieve(
            "tenant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tenant = response.parse()
            assert_matches_type(Tenant, tenant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Rocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tenant_id` but received ''"):
            client.tenants.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Rocktick) -> None:
        tenant = client.tenants.update(
            tenant_id="tenant_id",
        )
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Rocktick) -> None:
        tenant = client.tenants.update(
            tenant_id="tenant_id",
            default_retries=0,
            max_max_response_bytes=0,
            max_request_bytes=0,
            max_timeout=0,
            max_tokens=0,
            tok_per_day=0,
            tokens=0,
        )
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Rocktick) -> None:
        response = client.tenants.with_raw_response.update(
            tenant_id="tenant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tenant = response.parse()
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Rocktick) -> None:
        with client.tenants.with_streaming_response.update(
            tenant_id="tenant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tenant = response.parse()
            assert_matches_type(Tenant, tenant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Rocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tenant_id` but received ''"):
            client.tenants.with_raw_response.update(
                tenant_id="",
            )


class TestAsyncTenants:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncRocktick) -> None:
        tenant = await async_client.tenants.create(
            default_retries=0,
            max_max_response_bytes=0,
            max_request_bytes=0,
            max_timeout=0,
            max_tokens=0,
            tok_per_day=0,
        )
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncRocktick) -> None:
        response = await async_client.tenants.with_raw_response.create(
            default_retries=0,
            max_max_response_bytes=0,
            max_request_bytes=0,
            max_timeout=0,
            max_tokens=0,
            tok_per_day=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tenant = await response.parse()
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncRocktick) -> None:
        async with async_client.tenants.with_streaming_response.create(
            default_retries=0,
            max_max_response_bytes=0,
            max_request_bytes=0,
            max_timeout=0,
            max_tokens=0,
            tok_per_day=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tenant = await response.parse()
            assert_matches_type(Tenant, tenant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncRocktick) -> None:
        tenant = await async_client.tenants.retrieve(
            "tenant_id",
        )
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncRocktick) -> None:
        response = await async_client.tenants.with_raw_response.retrieve(
            "tenant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tenant = await response.parse()
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncRocktick) -> None:
        async with async_client.tenants.with_streaming_response.retrieve(
            "tenant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tenant = await response.parse()
            assert_matches_type(Tenant, tenant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncRocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tenant_id` but received ''"):
            await async_client.tenants.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncRocktick) -> None:
        tenant = await async_client.tenants.update(
            tenant_id="tenant_id",
        )
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncRocktick) -> None:
        tenant = await async_client.tenants.update(
            tenant_id="tenant_id",
            default_retries=0,
            max_max_response_bytes=0,
            max_request_bytes=0,
            max_timeout=0,
            max_tokens=0,
            tok_per_day=0,
            tokens=0,
        )
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncRocktick) -> None:
        response = await async_client.tenants.with_raw_response.update(
            tenant_id="tenant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tenant = await response.parse()
        assert_matches_type(Tenant, tenant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncRocktick) -> None:
        async with async_client.tenants.with_streaming_response.update(
            tenant_id="tenant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tenant = await response.parse()
            assert_matches_type(Tenant, tenant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncRocktick) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tenant_id` but received ''"):
            await async_client.tenants.with_raw_response.update(
                tenant_id="",
            )
