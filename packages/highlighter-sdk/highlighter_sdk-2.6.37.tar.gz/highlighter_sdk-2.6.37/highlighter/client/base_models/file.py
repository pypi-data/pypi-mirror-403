from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ...core import GQLBaseModel
from .page_info import PageInfo

__all__ = ["File", "FilePresigned", "FileConnection"]


class File(GQLBaseModel):
    """GraphQL File type response model"""

    id: str
    uuid: UUID
    content_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    original_source_url: str
    mime_type: Optional[str] = None
    recorded_at: Optional[datetime] = None


class FilePresigned(File):
    file_url_original: str


class FileConnection(GQLBaseModel):
    page_info: PageInfo
    nodes: List[FilePresigned]
