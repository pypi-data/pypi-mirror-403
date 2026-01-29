# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from eos import EOS, AsyncEOS
from tests.utils import assert_matches_type
from eos.types.v1 import (
    MemoryListResponse,
    MemoryCreateResponse,
    MemoryDeleteResponse,
    MemorySearchResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMemories:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: EOS) -> None:
        memory = client.v1.memories.create(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        )
        assert_matches_type(MemoryCreateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: EOS) -> None:
        memory = client.v1.memories.create(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
            group_id="group_123",
            group_name="Project Discussion Group",
            refer_list=["msg_000"],
            role="user",
            sender_name="John",
        )
        assert_matches_type(MemoryCreateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: EOS) -> None:
        response = client.v1.memories.with_raw_response.create(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryCreateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: EOS) -> None:
        with client.v1.memories.with_streaming_response.create(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryCreateResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: EOS) -> None:
        memory = client.v1.memories.list()
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: EOS) -> None:
        response = client.v1.memories.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: EOS) -> None:
        with client.v1.memories.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryListResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: EOS) -> None:
        memory = client.v1.memories.delete()
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_with_all_params(self, client: EOS) -> None:
        memory = client.v1.memories.delete(
            event_id="507f1f77bcf86cd799439011",
            group_id="group_456",
            user_id="user_123",
        )
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: EOS) -> None:
        response = client.v1.memories.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: EOS) -> None:
        with client.v1.memories.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_search(self, client: EOS) -> None:
        memory = client.v1.memories.search()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_search(self, client: EOS) -> None:
        response = client.v1.memories.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = response.parse()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_search(self, client: EOS) -> None:
        with client.v1.memories.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = response.parse()
            assert_matches_type(MemorySearchResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMemories:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncEOS) -> None:
        memory = await async_client.v1.memories.create(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        )
        assert_matches_type(MemoryCreateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncEOS) -> None:
        memory = await async_client.v1.memories.create(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
            group_id="group_123",
            group_name="Project Discussion Group",
            refer_list=["msg_000"],
            role="user",
            sender_name="John",
        )
        assert_matches_type(MemoryCreateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncEOS) -> None:
        response = await async_client.v1.memories.with_raw_response.create(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryCreateResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncEOS) -> None:
        async with async_client.v1.memories.with_streaming_response.create(
            content="Let's discuss the technical solution for the new feature today",
            create_time="2025-01-15T10:00:00+00:00",
            message_id="msg_001",
            sender="user_001",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryCreateResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncEOS) -> None:
        memory = await async_client.v1.memories.list()
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncEOS) -> None:
        response = await async_client.v1.memories.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryListResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncEOS) -> None:
        async with async_client.v1.memories.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryListResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncEOS) -> None:
        memory = await async_client.v1.memories.delete()
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_with_all_params(self, async_client: AsyncEOS) -> None:
        memory = await async_client.v1.memories.delete(
            event_id="507f1f77bcf86cd799439011",
            group_id="group_456",
            user_id="user_123",
        )
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncEOS) -> None:
        response = await async_client.v1.memories.with_raw_response.delete()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncEOS) -> None:
        async with async_client.v1.memories.with_streaming_response.delete() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemoryDeleteResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_search(self, async_client: AsyncEOS) -> None:
        memory = await async_client.v1.memories.search()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_search(self, async_client: AsyncEOS) -> None:
        response = await async_client.v1.memories.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        memory = await response.parse()
        assert_matches_type(MemorySearchResponse, memory, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncEOS) -> None:
        async with async_client.v1.memories.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            memory = await response.parse()
            assert_matches_type(MemorySearchResponse, memory, path=["response"])

        assert cast(Any, response.is_closed) is True
