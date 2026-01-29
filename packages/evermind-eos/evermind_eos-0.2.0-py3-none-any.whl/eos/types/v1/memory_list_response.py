# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from .metadata import Metadata
from ..._models import BaseModel

__all__ = [
    "MemoryListResponse",
    "Result",
    "ResultMemory",
    "ResultMemoryProfileModel",
    "ResultMemoryEpisodicMemoryModel",
    "ResultMemoryEventLogModel",
    "ResultMemoryForesightModel",
]


class ResultMemoryProfileModel(BaseModel):
    id: str

    group_id: str

    user_id: str

    cluster_ids: Optional[List[str]] = None

    confidence: Optional[float] = None

    created_at: Optional[datetime] = None

    last_updated_cluster: Optional[str] = None

    memcell_count: Optional[int] = None

    profile_data: Optional[Dict[str, object]] = None

    scenario: Optional[str] = None

    updated_at: Optional[datetime] = None

    version: Optional[int] = None


class ResultMemoryEpisodicMemoryModel(BaseModel):
    id: str

    episode_id: str

    summary: str

    title: str

    user_id: str

    created_at: Optional[datetime] = None

    end_time: Optional[datetime] = None

    extend: Optional[Dict[str, object]] = None

    group_id: Optional[str] = None

    group_name: Optional[str] = None

    key_events: Optional[List[str]] = None

    location: Optional[str] = None

    memcell_event_id_list: Optional[List[str]] = None

    metadata: Optional[Metadata] = None

    participants: Optional[List[str]] = None

    start_time: Optional[datetime] = None

    subject: Optional[str] = None

    timestamp: Optional[datetime] = None

    updated_at: Optional[datetime] = None


class ResultMemoryEventLogModel(BaseModel):
    id: str

    atomic_fact: str

    parent_id: str

    parent_type: str

    timestamp: datetime

    user_id: str

    created_at: Optional[datetime] = None

    event_type: Optional[str] = None

    extend: Optional[Dict[str, object]] = None

    group_id: Optional[str] = None

    group_name: Optional[str] = None

    metadata: Optional[Metadata] = None

    participants: Optional[List[str]] = None

    updated_at: Optional[datetime] = None

    user_name: Optional[str] = None

    vector: Optional[List[float]] = None

    vector_model: Optional[str] = None


class ResultMemoryForesightModel(BaseModel):
    id: str

    content: str

    parent_id: str

    parent_type: str

    created_at: Optional[datetime] = None

    duration_days: Optional[int] = None

    end_time: Optional[str] = None

    evidence: Optional[str] = None

    extend: Optional[Dict[str, object]] = None

    group_id: Optional[str] = None

    group_name: Optional[str] = None

    metadata: Optional[Metadata] = None

    participants: Optional[List[str]] = None

    start_time: Optional[str] = None

    updated_at: Optional[datetime] = None

    user_id: Optional[str] = None

    user_name: Optional[str] = None

    vector: Optional[List[float]] = None

    vector_model: Optional[str] = None


ResultMemory: TypeAlias = Union[
    ResultMemoryProfileModel, ResultMemoryEpisodicMemoryModel, ResultMemoryEventLogModel, ResultMemoryForesightModel
]


class Result(BaseModel):
    """Memory fetch result"""

    has_more: Optional[bool] = None

    memories: Optional[List[ResultMemory]] = None

    metadata: Optional[Metadata] = None

    total_count: Optional[int] = None


class MemoryListResponse(BaseModel):
    """Memory fetch API response

    Response for GET /api/v1/memories endpoint.
    """

    result: Result
    """Memory fetch result"""

    message: Optional[str] = None
    """Response message"""

    status: Optional[str] = None
    """Response status"""
