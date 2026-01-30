# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ObjectListResponse", "Object"]


class Object(BaseModel):
    id: Optional[str] = None
    """Unique object identifier"""

    chunk_count: Optional[float] = FieldInfo(alias="chunkCount", default=None)
    """Number of text chunks created for vectorization"""

    content_type: Optional[str] = FieldInfo(alias="contentType", default=None)
    """MIME type of the document"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Document upload timestamp"""

    filename: Optional[str] = None
    """Original filename of the uploaded document"""

    ingestion_completed_at: Optional[datetime] = FieldInfo(alias="ingestionCompletedAt", default=None)
    """Processing completion timestamp"""

    ingestion_status: Optional[str] = FieldInfo(alias="ingestionStatus", default=None)
    """Processing status of the document"""

    metadata: Optional[object] = None
    """Custom metadata associated with the document"""

    page_count: Optional[float] = FieldInfo(alias="pageCount", default=None)
    """Number of pages in the document"""

    path: Optional[str] = None
    """Optional folder path for hierarchy preservation from source systems"""

    size_bytes: Optional[float] = FieldInfo(alias="sizeBytes", default=None)
    """File size in bytes"""

    tags: Optional[List[str]] = None
    """Custom tags associated with the document"""

    text_length: Optional[float] = FieldInfo(alias="textLength", default=None)
    """Total character count of extracted text"""

    vector_count: Optional[float] = FieldInfo(alias="vectorCount", default=None)
    """Number of vectors generated for semantic search"""


class ObjectListResponse(BaseModel):
    count: Optional[float] = None
    """Total number of objects in the vault"""

    objects: Optional[List[Object]] = None

    vault_id: Optional[str] = FieldInfo(alias="vaultId", default=None)
    """The ID of the vault"""
