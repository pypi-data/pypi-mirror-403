# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["MemoryCreateResponse", "Result"]


class Result(BaseModel):
    """Memory storage result"""

    count: Optional[int] = None
    """Number of memories extracted"""

    saved_memories: Optional[List[object]] = None
    """List of saved memories (fetch via API for details)"""

    status_info: Optional[str] = None
    """
    Processing status: 'extracted' (memories created) or 'accumulated' (waiting for
    boundary)
    """


class MemoryCreateResponse(BaseModel):
    """Memory storage response

    Response for POST /api/v1/memories endpoint.
    """

    message: Optional[str] = None
    """Response message"""

    result: Optional[Result] = None
    """Memory storage result"""

    status: Optional[str] = None
    """Response status"""
