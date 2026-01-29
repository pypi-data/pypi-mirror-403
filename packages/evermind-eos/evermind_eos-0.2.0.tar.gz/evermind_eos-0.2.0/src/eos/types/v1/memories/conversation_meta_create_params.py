# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, TypedDict

from ...._types import SequenceNotStr

__all__ = ["ConversationMetaCreateParams", "UserDetails"]


class ConversationMetaCreateParams(TypedDict, total=False):
    created_at: Required[str]
    """Conversation creation time (ISO 8601 format)"""

    name: Required[str]
    """Conversation name"""

    scene: Required[str]
    """Scene identifier, enum values from ScenarioType:

    - group_chat: work/group chat scenario, suitable for group conversations such as
      multi-person collaboration and project discussions
    - assistant: assistant scenario, suitable for one-on-one AI assistant
      conversations
    """

    scene_desc: Required[Dict[str, object]]
    """Scene description object, can include fields like description"""

    version: Required[str]
    """Metadata version number"""

    default_timezone: Optional[str]
    """Default timezone"""

    description: Optional[str]
    """Conversation description"""

    group_id: Optional[str]
    """Group unique identifier.

    When null/not provided, represents default settings for this scene.
    """

    tags: Optional[SequenceNotStr[str]]
    """Tag list"""

    user_details: Optional[Dict[str, UserDetails]]
    """Participant details, key is user ID, value is user detail object"""


class UserDetails(TypedDict, total=False):
    """User details

    Structure for the value of ConversationMetaRequest.user_details
    """

    custom_role: Optional[str]
    """User's job/position role (e.g. developer, designer, manager)"""

    extra: Optional[Dict[str, object]]
    """Additional information"""

    full_name: Optional[str]
    """User full name"""

    role: Optional[str]
    """
    User type role, used to identify if this user is a human or AI. Enum values from
    MessageSenderRole:

    - user: Human user
    - assistant: AI assistant/bot
    """
