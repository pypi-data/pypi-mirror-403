# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from labric import Labric, AsyncLabric
from tests.utils import assert_matches_type
from labric.types import ToolReadResponse, ToolWriteResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTools:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_read(self, client: Labric) -> None:
        tool = client.tools.read(
            filters={"name": "bar"},
            target_name="samples",
            target_type="table",
        )
        assert_matches_type(ToolReadResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_read_with_all_params(self, client: Labric) -> None:
        tool = client.tools.read(
            filters={"name": "bar"},
            target_name="samples",
            target_type="table",
            mode="single",
        )
        assert_matches_type(ToolReadResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_read(self, client: Labric) -> None:
        response = client.tools.with_raw_response.read(
            filters={"name": "bar"},
            target_name="samples",
            target_type="table",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = response.parse()
        assert_matches_type(ToolReadResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_read(self, client: Labric) -> None:
        with client.tools.with_streaming_response.read(
            filters={"name": "bar"},
            target_name="samples",
            target_type="table",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = response.parse()
            assert_matches_type(ToolReadResponse, tool, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_write(self, client: Labric) -> None:
        tool = client.tools.write(
            data=[
                {
                    "concentration": "bar",
                    "name": "bar",
                },
                {
                    "concentration": "bar",
                    "name": "bar",
                },
            ],
            mode="create",
            target_name="samples",
            target_type="table",
        )
        assert_matches_type(ToolWriteResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_write_with_all_params(self, client: Labric) -> None:
        tool = client.tools.write(
            data=[
                {
                    "concentration": "bar",
                    "name": "bar",
                },
                {
                    "concentration": "bar",
                    "name": "bar",
                },
            ],
            mode="create",
            target_name="samples",
            target_type="table",
            batch_insert_ok=True,
            collect_output=True,
            defaults={
                "created_at": "DATETIME_NOW",
                "id": "UUID4",
            },
            dry_run=True,
            job_execution_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            job_name="job_name",
            params_to_match_for_update=["name"],
        )
        assert_matches_type(ToolWriteResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_write(self, client: Labric) -> None:
        response = client.tools.with_raw_response.write(
            data=[
                {
                    "concentration": "bar",
                    "name": "bar",
                },
                {
                    "concentration": "bar",
                    "name": "bar",
                },
            ],
            mode="create",
            target_name="samples",
            target_type="table",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = response.parse()
        assert_matches_type(ToolWriteResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_write(self, client: Labric) -> None:
        with client.tools.with_streaming_response.write(
            data=[
                {
                    "concentration": "bar",
                    "name": "bar",
                },
                {
                    "concentration": "bar",
                    "name": "bar",
                },
            ],
            mode="create",
            target_name="samples",
            target_type="table",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = response.parse()
            assert_matches_type(ToolWriteResponse, tool, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncTools:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_read(self, async_client: AsyncLabric) -> None:
        tool = await async_client.tools.read(
            filters={"name": "bar"},
            target_name="samples",
            target_type="table",
        )
        assert_matches_type(ToolReadResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_read_with_all_params(self, async_client: AsyncLabric) -> None:
        tool = await async_client.tools.read(
            filters={"name": "bar"},
            target_name="samples",
            target_type="table",
            mode="single",
        )
        assert_matches_type(ToolReadResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_read(self, async_client: AsyncLabric) -> None:
        response = await async_client.tools.with_raw_response.read(
            filters={"name": "bar"},
            target_name="samples",
            target_type="table",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = await response.parse()
        assert_matches_type(ToolReadResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_read(self, async_client: AsyncLabric) -> None:
        async with async_client.tools.with_streaming_response.read(
            filters={"name": "bar"},
            target_name="samples",
            target_type="table",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = await response.parse()
            assert_matches_type(ToolReadResponse, tool, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_write(self, async_client: AsyncLabric) -> None:
        tool = await async_client.tools.write(
            data=[
                {
                    "concentration": "bar",
                    "name": "bar",
                },
                {
                    "concentration": "bar",
                    "name": "bar",
                },
            ],
            mode="create",
            target_name="samples",
            target_type="table",
        )
        assert_matches_type(ToolWriteResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_write_with_all_params(self, async_client: AsyncLabric) -> None:
        tool = await async_client.tools.write(
            data=[
                {
                    "concentration": "bar",
                    "name": "bar",
                },
                {
                    "concentration": "bar",
                    "name": "bar",
                },
            ],
            mode="create",
            target_name="samples",
            target_type="table",
            batch_insert_ok=True,
            collect_output=True,
            defaults={
                "created_at": "DATETIME_NOW",
                "id": "UUID4",
            },
            dry_run=True,
            job_execution_id="182bd5e5-6e1a-4fe4-a799-aa6d9a6ab26e",
            job_name="job_name",
            params_to_match_for_update=["name"],
        )
        assert_matches_type(ToolWriteResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_write(self, async_client: AsyncLabric) -> None:
        response = await async_client.tools.with_raw_response.write(
            data=[
                {
                    "concentration": "bar",
                    "name": "bar",
                },
                {
                    "concentration": "bar",
                    "name": "bar",
                },
            ],
            mode="create",
            target_name="samples",
            target_type="table",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tool = await response.parse()
        assert_matches_type(ToolWriteResponse, tool, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_write(self, async_client: AsyncLabric) -> None:
        async with async_client.tools.with_streaming_response.write(
            data=[
                {
                    "concentration": "bar",
                    "name": "bar",
                },
                {
                    "concentration": "bar",
                    "name": "bar",
                },
            ],
            mode="create",
            target_name="samples",
            target_type="table",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tool = await response.parse()
            assert_matches_type(ToolWriteResponse, tool, path=["response"])

        assert cast(Any, response.is_closed) is True
