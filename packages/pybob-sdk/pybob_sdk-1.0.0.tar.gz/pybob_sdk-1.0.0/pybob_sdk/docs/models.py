"""Models for the Documents API domain."""

from datetime import datetime

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


class DocumentFolder(BobModel):
    """A document folder."""

    id: str | None = None
    name: str | None = None
    folder_type: str | None = Field(default=None, alias="folderType")
    description: str | None = None


class Document(BobModel):
    """A document in Bob."""

    id: str | None = None
    name: str | None = None
    folder_id: str | None = Field(default=None, alias="folderId")
    folder_name: str | None = Field(default=None, alias="folderName")
    uploaded_at: datetime | None = Field(default=None, alias="uploadedAt")
    uploaded_by: str | None = Field(default=None, alias="uploadedBy")
    file_type: str | None = Field(default=None, alias="fileType")
    file_size: int | None = Field(default=None, alias="fileSize")
    url: str | None = None


class DocumentUploadRequest(BobModel):
    """Request body for uploading a document."""

    file_name: str = Field(alias="fileName")
    document_name: str | None = Field(default=None, alias="documentName")
    tags: list[str] = Field(default_factory=list)


class DocumentUploadUrlRequest(BobModel):
    """Request body for uploading a document from a URL."""

    url: str
    document_name: str | None = Field(default=None, alias="documentName")
    tags: list[str] = Field(default_factory=list)


class FoldersResponse(BobModel):
    """Response containing document folders."""

    folders: list[DocumentFolder] = Field(default_factory=list)


class DocumentsResponse(BobModel):
    """Response containing documents."""

    documents: list[Document] = Field(default_factory=list)
