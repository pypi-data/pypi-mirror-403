# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import TypedDict

__all__ = ["MemoryDeleteParams"]


class MemoryDeleteParams(TypedDict, total=False):
    event_id: Optional[str]
    """Memory event_id (filter condition)"""

    group_id: Optional[str]
    """Group ID (filter condition)"""

    user_id: Optional[str]
    """User ID (filter condition)"""
