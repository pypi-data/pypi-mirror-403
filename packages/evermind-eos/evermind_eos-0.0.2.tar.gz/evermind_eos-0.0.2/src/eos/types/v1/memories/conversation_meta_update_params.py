# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import TypedDict

from ...._types import SequenceNotStr

__all__ = ["ConversationMetaUpdateParams", "UserDetails"]


class ConversationMetaUpdateParams(TypedDict, total=False):
    default_timezone: Optional[str]
    """New default timezone"""

    description: Optional[str]
    """New conversation description"""

    group_id: Optional[str]
    """Group ID to update. When null, updates the default config."""

    name: Optional[str]
    """New conversation name"""

    scene_desc: Optional[Dict[str, object]]
    """New scene description"""

    tags: Optional[SequenceNotStr[str]]
    """New tag list"""

    user_details: Optional[Dict[str, UserDetails]]
    """New user details (will completely replace existing user_details)"""


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
