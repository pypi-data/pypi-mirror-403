# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ObjectRetrieveResponse"]


class ObjectRetrieveResponse(BaseModel):
    id: Optional[str] = None
    """Object ID"""

    chunk_count: Optional[int] = FieldInfo(alias="chunkCount", default=None)
    """Number of text chunks created"""

    content_type: Optional[str] = FieldInfo(alias="contentType", default=None)
    """MIME type"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Upload timestamp"""

    download_url: Optional[str] = FieldInfo(alias="downloadUrl", default=None)
    """Presigned S3 download URL"""

    expires_in: Optional[int] = FieldInfo(alias="expiresIn", default=None)
    """URL expiration time in seconds"""

    filename: Optional[str] = None
    """Original filename"""

    ingestion_status: Optional[str] = FieldInfo(alias="ingestionStatus", default=None)
    """Processing status (pending, processing, completed, failed)"""

    metadata: Optional[object] = None
    """Additional metadata"""

    page_count: Optional[int] = FieldInfo(alias="pageCount", default=None)
    """Number of pages (for documents)"""

    path: Optional[str] = None
    """Optional folder path for hierarchy preservation"""

    size_bytes: Optional[int] = FieldInfo(alias="sizeBytes", default=None)
    """File size in bytes"""

    text_length: Optional[int] = FieldInfo(alias="textLength", default=None)
    """Length of extracted text"""

    vault_id: Optional[str] = FieldInfo(alias="vaultId", default=None)
    """Vault ID"""

    vector_count: Optional[int] = FieldInfo(alias="vectorCount", default=None)
    """Number of embedding vectors generated"""
