# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from ..._models import BaseModel

__all__ = ["ObjectGetTextResponse", "Metadata"]


class Metadata(BaseModel):
    chunk_count: Optional[int] = None
    """Number of text chunks the document was split into"""

    filename: Optional[str] = None
    """Original filename of the document"""

    ingestion_completed_at: Optional[datetime] = None
    """When the document processing completed"""

    length: Optional[int] = None
    """Total character count of the extracted text"""

    object_id: Optional[str] = None
    """The object ID"""

    vault_id: Optional[str] = None
    """The vault ID"""


class ObjectGetTextResponse(BaseModel):
    metadata: Optional[Metadata] = None

    text: Optional[str] = None
    """Full concatenated text content from all chunks"""
