# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from eos import EOS, AsyncEOS
from tests.utils import assert_matches_type
from eos.types.v1.memories import (
    ConversationMetaCreateResponse,
    ConversationMetaUpdateResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestConversationMeta:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: EOS) -> None:
        conversation_meta = client.v1.memories.conversation_meta.create(
            created_at="2025-01-15T10:00:00+00:00",
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            version="1.0",
        )
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: EOS) -> None:
        conversation_meta = client.v1.memories.conversation_meta.create(
            created_at="2025-01-15T10:00:00+00:00",
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            version="1.0",
            default_timezone="UTC",
            description="Technical discussion for new feature development",
            group_id="group_123",
            tags=["work", "technical"],
            user_details={
                "bot_001": {
                    "custom_role": "assistant",
                    "extra": {"type": "bar"},
                    "full_name": "AI Assistant",
                    "role": "assistant",
                },
                "user_001": {
                    "custom_role": "developer",
                    "extra": {"department": "bar"},
                    "full_name": "John Smith",
                    "role": "user",
                },
            },
        )
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: EOS) -> None:
        response = client.v1.memories.conversation_meta.with_raw_response.create(
            created_at="2025-01-15T10:00:00+00:00",
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            version="1.0",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = response.parse()
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: EOS) -> None:
        with client.v1.memories.conversation_meta.with_streaming_response.create(
            created_at="2025-01-15T10:00:00+00:00",
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            version="1.0",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = response.parse()
            assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: EOS) -> None:
        conversation_meta = client.v1.memories.conversation_meta.update()
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: EOS) -> None:
        conversation_meta = client.v1.memories.conversation_meta.update(
            default_timezone="Asia/Shanghai",
            description="Updated description",
            group_id="group_123",
            name="New Conversation Name",
            scene_desc={"description": "bar"},
            tags=["tag1", "tag2"],
            user_details={
                "user_001": {
                    "custom_role": "lead",
                    "extra": {"department": "bar"},
                    "full_name": "John Smith",
                    "role": "user",
                }
            },
        )
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: EOS) -> None:
        response = client.v1.memories.conversation_meta.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = response.parse()
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: EOS) -> None:
        with client.v1.memories.conversation_meta.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = response.parse()
            assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncConversationMeta:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncEOS) -> None:
        conversation_meta = await async_client.v1.memories.conversation_meta.create(
            created_at="2025-01-15T10:00:00+00:00",
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            version="1.0",
        )
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncEOS) -> None:
        conversation_meta = await async_client.v1.memories.conversation_meta.create(
            created_at="2025-01-15T10:00:00+00:00",
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            version="1.0",
            default_timezone="UTC",
            description="Technical discussion for new feature development",
            group_id="group_123",
            tags=["work", "technical"],
            user_details={
                "bot_001": {
                    "custom_role": "assistant",
                    "extra": {"type": "bar"},
                    "full_name": "AI Assistant",
                    "role": "assistant",
                },
                "user_001": {
                    "custom_role": "developer",
                    "extra": {"department": "bar"},
                    "full_name": "John Smith",
                    "role": "user",
                },
            },
        )
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncEOS) -> None:
        response = await async_client.v1.memories.conversation_meta.with_raw_response.create(
            created_at="2025-01-15T10:00:00+00:00",
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            version="1.0",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = await response.parse()
        assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncEOS) -> None:
        async with async_client.v1.memories.conversation_meta.with_streaming_response.create(
            created_at="2025-01-15T10:00:00+00:00",
            name="Project Discussion Group",
            scene="group_chat",
            scene_desc={
                "description": "bar",
                "type": "bar",
            },
            version="1.0",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = await response.parse()
            assert_matches_type(ConversationMetaCreateResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncEOS) -> None:
        conversation_meta = await async_client.v1.memories.conversation_meta.update()
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncEOS) -> None:
        conversation_meta = await async_client.v1.memories.conversation_meta.update(
            default_timezone="Asia/Shanghai",
            description="Updated description",
            group_id="group_123",
            name="New Conversation Name",
            scene_desc={"description": "bar"},
            tags=["tag1", "tag2"],
            user_details={
                "user_001": {
                    "custom_role": "lead",
                    "extra": {"department": "bar"},
                    "full_name": "John Smith",
                    "role": "user",
                }
            },
        )
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncEOS) -> None:
        response = await async_client.v1.memories.conversation_meta.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        conversation_meta = await response.parse()
        assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncEOS) -> None:
        async with async_client.v1.memories.conversation_meta.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            conversation_meta = await response.parse()
            assert_matches_type(ConversationMetaUpdateResponse, conversation_meta, path=["response"])

        assert cast(Any, response.is_closed) is True
