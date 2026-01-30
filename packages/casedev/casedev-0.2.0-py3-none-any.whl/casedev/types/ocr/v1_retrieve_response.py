# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from ..._models import BaseModel

__all__ = ["V1RetrieveResponse"]


class V1RetrieveResponse(BaseModel):
    id: Optional[str] = None
    """OCR job ID"""

    completed_at: Optional[datetime] = None
    """Job completion timestamp"""

    created_at: Optional[datetime] = None
    """Job creation timestamp"""

    metadata: Optional[object] = None
    """Additional processing metadata"""

    page_count: Optional[int] = None
    """Number of pages processed"""

    status: Optional[Literal["pending", "processing", "completed", "failed"]] = None
    """Current job status"""

    text: Optional[str] = None
    """Extracted text content (when completed)"""
