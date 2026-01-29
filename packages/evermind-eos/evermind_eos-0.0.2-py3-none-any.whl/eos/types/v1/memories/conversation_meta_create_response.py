# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional

from ...._models import BaseModel

__all__ = ["ConversationMetaCreateResponse", "Result"]


class Result(BaseModel):
    """Saved conversation metadata"""

    id: str
    """Document ID"""

    conversation_created_at: str
    """Conversation creation time"""

    name: str
    """Conversation name"""

    scene: str
    """Scene identifier"""

    version: str
    """Metadata version"""

    created_at: Optional[str] = None
    """Record creation time"""

    default_timezone: Optional[str] = None
    """Default timezone"""

    description: Optional[str] = None
    """Conversation description"""

    group_id: Optional[str] = None
    """Group ID (null for default config)"""

    is_default: Optional[bool] = None
    """Whether this is the default config"""

    scene_desc: Optional[Dict[str, object]] = None
    """Scene description"""

    tags: Optional[List[str]] = None
    """Tags"""

    updated_at: Optional[str] = None
    """Record update time"""

    user_details: Optional[Dict[str, Dict[str, object]]] = None
    """User details"""


class ConversationMetaCreateResponse(BaseModel):
    """Save conversation metadata API response

    Response for POST /api/v1/memories/conversation-meta endpoint.
    """

    result: Result
    """Saved conversation metadata"""

    message: Optional[str] = None
    """Response message"""

    status: Optional[str] = None
    """Response status"""
