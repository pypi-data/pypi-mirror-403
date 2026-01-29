# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.v1.memories import conversation_meta_create_params, conversation_meta_update_params
from ....types.v1.memories.conversation_meta_create_response import ConversationMetaCreateResponse
from ....types.v1.memories.conversation_meta_update_response import ConversationMetaUpdateResponse

__all__ = ["ConversationMetaResource", "AsyncConversationMetaResource"]


class ConversationMetaResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ConversationMetaResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/stainless-sdks/eos-python#accessing-raw-response-data-eg-headers
        """
        return ConversationMetaResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ConversationMetaResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/stainless-sdks/eos-python#with_streaming_response
        """
        return ConversationMetaResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        created_at: str,
        name: str,
        scene: str,
        scene_desc: Dict[str, object],
        version: str,
        default_timezone: Optional[str] | Omit = omit,
        description: Optional[str] | Omit = omit,
        group_id: Optional[str] | Omit = omit,
        tags: Optional[SequenceNotStr[str]] | Omit = omit,
        user_details: Optional[Dict[str, conversation_meta_create_params.UserDetails]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationMetaCreateResponse:
        """
        Save conversation metadata information, including scene, participants, tags,
        etc.

                ## Functionality:
                - If group_id exists, update the entire record (upsert)
                - If group_id does not exist, create a new record
                - If group_id is omitted, save as default config for the scene
                - All fields must be provided with complete data

                ## Default Config:
                - Default config is used as fallback when specific group_id config not found

                ## Notes:
                - This is a full update interface that will replace the entire record
                - If you only need to update partial fields, use the PATCH /conversation-meta interface

        Args:
          created_at: Conversation creation time (ISO 8601 format)

          name: Conversation name

          scene:
              Scene identifier, enum values from ScenarioType:

              - group_chat: work/group chat scenario, suitable for group conversations such as
                multi-person collaboration and project discussions
              - assistant: assistant scenario, suitable for one-on-one AI assistant
                conversations

          scene_desc: Scene description object, can include fields like description

          version: Metadata version number

          default_timezone: Default timezone

          description: Conversation description

          group_id: Group unique identifier. When null/not provided, represents default settings for
              this scene.

          tags: Tag list

          user_details: Participant details, key is user ID, value is user detail object

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/v1/memories/conversation-meta",
            body=maybe_transform(
                {
                    "created_at": created_at,
                    "name": name,
                    "scene": scene,
                    "scene_desc": scene_desc,
                    "version": version,
                    "default_timezone": default_timezone,
                    "description": description,
                    "group_id": group_id,
                    "tags": tags,
                    "user_details": user_details,
                },
                conversation_meta_create_params.ConversationMetaCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationMetaCreateResponse,
        )

    def update(
        self,
        *,
        default_timezone: Optional[str] | Omit = omit,
        description: Optional[str] | Omit = omit,
        group_id: Optional[str] | Omit = omit,
        name: Optional[str] | Omit = omit,
        scene_desc: Optional[Dict[str, object]] | Omit = omit,
        tags: Optional[SequenceNotStr[str]] | Omit = omit,
        user_details: Optional[Dict[str, conversation_meta_update_params.UserDetails]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationMetaUpdateResponse:
        """
        Partially update conversation metadata, only updating provided fields

                ## Functionality:
                - Locate the conversation metadata to update by group_id
                - When group_id is null or not provided, updates the default config
                - Only update fields provided in the request, keep unchanged fields as-is
                - Suitable for scenarios requiring modification of partial information

        Args:
          default_timezone: New default timezone

          description: New conversation description

          group_id: Group ID to update. When null, updates the default config.

          name: New conversation name

          scene_desc: New scene description

          tags: New tag list

          user_details: New user details (will completely replace existing user_details)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._patch(
            "/api/v1/memories/conversation-meta",
            body=maybe_transform(
                {
                    "default_timezone": default_timezone,
                    "description": description,
                    "group_id": group_id,
                    "name": name,
                    "scene_desc": scene_desc,
                    "tags": tags,
                    "user_details": user_details,
                },
                conversation_meta_update_params.ConversationMetaUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationMetaUpdateResponse,
        )


class AsyncConversationMetaResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncConversationMetaResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/stainless-sdks/eos-python#accessing-raw-response-data-eg-headers
        """
        return AsyncConversationMetaResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncConversationMetaResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/stainless-sdks/eos-python#with_streaming_response
        """
        return AsyncConversationMetaResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        created_at: str,
        name: str,
        scene: str,
        scene_desc: Dict[str, object],
        version: str,
        default_timezone: Optional[str] | Omit = omit,
        description: Optional[str] | Omit = omit,
        group_id: Optional[str] | Omit = omit,
        tags: Optional[SequenceNotStr[str]] | Omit = omit,
        user_details: Optional[Dict[str, conversation_meta_create_params.UserDetails]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationMetaCreateResponse:
        """
        Save conversation metadata information, including scene, participants, tags,
        etc.

                ## Functionality:
                - If group_id exists, update the entire record (upsert)
                - If group_id does not exist, create a new record
                - If group_id is omitted, save as default config for the scene
                - All fields must be provided with complete data

                ## Default Config:
                - Default config is used as fallback when specific group_id config not found

                ## Notes:
                - This is a full update interface that will replace the entire record
                - If you only need to update partial fields, use the PATCH /conversation-meta interface

        Args:
          created_at: Conversation creation time (ISO 8601 format)

          name: Conversation name

          scene:
              Scene identifier, enum values from ScenarioType:

              - group_chat: work/group chat scenario, suitable for group conversations such as
                multi-person collaboration and project discussions
              - assistant: assistant scenario, suitable for one-on-one AI assistant
                conversations

          scene_desc: Scene description object, can include fields like description

          version: Metadata version number

          default_timezone: Default timezone

          description: Conversation description

          group_id: Group unique identifier. When null/not provided, represents default settings for
              this scene.

          tags: Tag list

          user_details: Participant details, key is user ID, value is user detail object

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/v1/memories/conversation-meta",
            body=await async_maybe_transform(
                {
                    "created_at": created_at,
                    "name": name,
                    "scene": scene,
                    "scene_desc": scene_desc,
                    "version": version,
                    "default_timezone": default_timezone,
                    "description": description,
                    "group_id": group_id,
                    "tags": tags,
                    "user_details": user_details,
                },
                conversation_meta_create_params.ConversationMetaCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationMetaCreateResponse,
        )

    async def update(
        self,
        *,
        default_timezone: Optional[str] | Omit = omit,
        description: Optional[str] | Omit = omit,
        group_id: Optional[str] | Omit = omit,
        name: Optional[str] | Omit = omit,
        scene_desc: Optional[Dict[str, object]] | Omit = omit,
        tags: Optional[SequenceNotStr[str]] | Omit = omit,
        user_details: Optional[Dict[str, conversation_meta_update_params.UserDetails]] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ConversationMetaUpdateResponse:
        """
        Partially update conversation metadata, only updating provided fields

                ## Functionality:
                - Locate the conversation metadata to update by group_id
                - When group_id is null or not provided, updates the default config
                - Only update fields provided in the request, keep unchanged fields as-is
                - Suitable for scenarios requiring modification of partial information

        Args:
          default_timezone: New default timezone

          description: New conversation description

          group_id: Group ID to update. When null, updates the default config.

          name: New conversation name

          scene_desc: New scene description

          tags: New tag list

          user_details: New user details (will completely replace existing user_details)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._patch(
            "/api/v1/memories/conversation-meta",
            body=await async_maybe_transform(
                {
                    "default_timezone": default_timezone,
                    "description": description,
                    "group_id": group_id,
                    "name": name,
                    "scene_desc": scene_desc,
                    "tags": tags,
                    "user_details": user_details,
                },
                conversation_meta_update_params.ConversationMetaUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ConversationMetaUpdateResponse,
        )


class ConversationMetaResourceWithRawResponse:
    def __init__(self, conversation_meta: ConversationMetaResource) -> None:
        self._conversation_meta = conversation_meta

        self.create = to_raw_response_wrapper(
            conversation_meta.create,
        )
        self.update = to_raw_response_wrapper(
            conversation_meta.update,
        )


class AsyncConversationMetaResourceWithRawResponse:
    def __init__(self, conversation_meta: AsyncConversationMetaResource) -> None:
        self._conversation_meta = conversation_meta

        self.create = async_to_raw_response_wrapper(
            conversation_meta.create,
        )
        self.update = async_to_raw_response_wrapper(
            conversation_meta.update,
        )


class ConversationMetaResourceWithStreamingResponse:
    def __init__(self, conversation_meta: ConversationMetaResource) -> None:
        self._conversation_meta = conversation_meta

        self.create = to_streamed_response_wrapper(
            conversation_meta.create,
        )
        self.update = to_streamed_response_wrapper(
            conversation_meta.update,
        )


class AsyncConversationMetaResourceWithStreamingResponse:
    def __init__(self, conversation_meta: AsyncConversationMetaResource) -> None:
        self._conversation_meta = conversation_meta

        self.create = async_to_streamed_response_wrapper(
            conversation_meta.create,
        )
        self.update = async_to_streamed_response_wrapper(
            conversation_meta.update,
        )
