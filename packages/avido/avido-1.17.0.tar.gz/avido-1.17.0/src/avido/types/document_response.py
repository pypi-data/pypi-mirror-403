# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["DocumentResponse", "Document", "DocumentVersion", "DocumentScrapeJob", "DocumentScrapeJobPage"]


class DocumentVersion(BaseModel):
    """A specific version of a document with its content and metadata"""

    id: str
    """Unique identifier of the document version"""

    content: str
    """Content of the document version"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the document version was created"""

    document_id: str = FieldInfo(alias="documentId")
    """ID of the document this version belongs to"""

    language: str
    """Language of the document version"""

    metadata: Dict[str, object]
    """Optional metadata associated with the document version"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the document version was last modified"""

    org_id: str = FieldInfo(alias="orgId")
    """Organization ID that owns this document version"""

    original_sentences: List[str] = FieldInfo(alias="originalSentences")
    """Array of original sentences from the source"""

    status: Literal["DRAFT", "REVIEW", "APPROVED", "ARCHIVED"]
    """Status of the document. Valid options: DRAFT, REVIEW, APPROVED, ARCHIVED."""

    title: str
    """Title of the document version"""

    version_number: int = FieldInfo(alias="versionNumber")
    """Version number of this document version"""


class DocumentScrapeJobPage(BaseModel):
    url: str
    """The URL of the page"""

    category: Optional[str] = None
    """The category of the page"""

    description: Optional[str] = None
    """The description of the page"""

    title: Optional[str] = None
    """The title of the page"""


class DocumentScrapeJob(BaseModel):
    """Optional scrape job that generated this document"""

    id: str
    """The unique identifier of the scrape job"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the scrape job was created"""

    initiated_by: str = FieldInfo(alias="initiatedBy")
    """User ID who initiated the scrape job"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the scrape job was last modified"""

    name: str
    """The name/title of the scrape job"""

    org_id: str = FieldInfo(alias="orgId")
    """Organization ID that owns the scrape job"""

    status: Literal["MAPPING", "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]
    """Current status of the scrape job"""

    url: str
    """The URL that was scraped"""

    pages: Optional[List[DocumentScrapeJobPage]] = None
    """The pages scraped from the URL"""


class Document(BaseModel):
    id: str
    """Unique identifier of the document"""

    assignee: str
    """User ID of the person assigned to this document"""

    content: str
    """use versions.content"""

    created_at: datetime = FieldInfo(alias="createdAt")
    """When the document was created"""

    modified_at: datetime = FieldInfo(alias="modifiedAt")
    """When the document was last modified"""

    optimized: bool
    """Whether the document has been optimized"""

    org_id: str = FieldInfo(alias="orgId")
    """Organization ID that owns this document"""

    title: str
    """use versions.title instead"""

    versions: List[DocumentVersion]
    """Array of document versions"""

    active_version_id: Optional[str] = FieldInfo(alias="activeVersionId", default=None)
    """ID of the currently active version of this document"""

    scrape_job: Optional[DocumentScrapeJob] = FieldInfo(alias="scrapeJob", default=None)
    """Optional scrape job that generated this document"""

    scrape_job_id: Optional[str] = FieldInfo(alias="scrapeJobId", default=None)
    """Optional ID of the scrape job that generated this document"""


class DocumentResponse(BaseModel):
    """Successful response containing the document data"""

    document: Document
