"""Documents API endpoints."""

from typing import BinaryIO

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.docs.models import (
    Document,
    DocumentFolder,
    DocumentsResponse,
    DocumentUploadUrlRequest,
    FoldersResponse,
)


class DocsAPI(BaseAPI):
    """API for managing documents in Bob."""

    async def get_folders(self) -> list[DocumentFolder]:
        """Get list of document folders with metadata.

        Returns:
            List of document folders.
        """
        response = await self._http.get("/docs/folders")
        parsed = self._parse_response(response, FoldersResponse)
        return parsed.folders

    async def get_employee_documents(self, employee_id: str) -> list[Document]:
        """Get list of documents for an employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of documents.
        """
        response = await self._http.get(f"/docs/people/{employee_id}")
        parsed = self._parse_response(response, DocumentsResponse)
        return parsed.documents

    # Shared Folder Methods
    async def upload_to_shared_folder_from_url(
        self,
        employee_id: str,
        request: DocumentUploadUrlRequest,
    ) -> Document:
        """Upload a file from a URL to an employee's shared folder.

        Args:
            employee_id: The employee ID.
            request: The upload request.

        Returns:
            The uploaded document.
        """
        response = await self._http.post(
            f"/docs/people/{employee_id}/shared/upload/url",
            json_data=request.to_api_dict(),
        )
        return self._parse_response(response, Document)

    async def upload_to_shared_folder(
        self,
        employee_id: str,
        file: BinaryIO,
        file_name: str,
        *,
        document_name: str | None = None,
    ) -> Document:
        """Upload a file to an employee's shared folder.

        Args:
            employee_id: The employee ID.
            file: The file to upload.
            file_name: The file name.
            document_name: Optional display name for the document.

        Returns:
            The uploaded document.
        """
        response = await self._http.post(
            f"/docs/people/{employee_id}/shared",
            files={"file": (file_name, file)},
            data={"documentName": document_name} if document_name else None,
        )
        return self._parse_response(response, Document)

    async def delete_from_shared_folder(
        self,
        employee_id: str,
        document_id: str,
    ) -> None:
        """Delete a document from an employee's shared folder.

        Args:
            employee_id: The employee ID.
            document_id: The document ID.
        """
        await self._http.delete(f"/docs/people/{employee_id}/shared/{document_id}")

    # Confidential Folder Methods
    async def upload_to_confidential_folder_from_url(
        self,
        employee_id: str,
        request: DocumentUploadUrlRequest,
    ) -> Document:
        """Upload a file from a URL to an employee's confidential folder.

        Args:
            employee_id: The employee ID.
            request: The upload request.

        Returns:
            The uploaded document.
        """
        response = await self._http.post(
            f"/docs/people/{employee_id}/confidential/upload/url",
            json_data=request.to_api_dict(),
        )
        return self._parse_response(response, Document)

    async def upload_to_confidential_folder(
        self,
        employee_id: str,
        file: BinaryIO,
        file_name: str,
        *,
        document_name: str | None = None,
    ) -> Document:
        """Upload a file to an employee's confidential folder.

        Args:
            employee_id: The employee ID.
            file: The file to upload.
            file_name: The file name.
            document_name: Optional display name for the document.

        Returns:
            The uploaded document.
        """
        response = await self._http.post(
            f"/docs/people/{employee_id}/confidential",
            files={"file": (file_name, file)},
            data={"documentName": document_name} if document_name else None,
        )
        return self._parse_response(response, Document)

    async def delete_from_confidential_folder(
        self,
        employee_id: str,
        document_id: str,
    ) -> None:
        """Delete a document from an employee's confidential folder.

        Args:
            employee_id: The employee ID.
            document_id: The document ID.
        """
        await self._http.delete(
            f"/docs/people/{employee_id}/confidential/{document_id}"
        )

    # Custom Folder Methods
    async def upload_to_custom_folder_from_url(
        self,
        employee_id: str,
        folder_id: str,
        request: DocumentUploadUrlRequest,
    ) -> Document:
        """Upload a file from a URL to a custom folder.

        Args:
            employee_id: The employee ID.
            folder_id: The folder ID.
            request: The upload request.

        Returns:
            The uploaded document.
        """
        response = await self._http.post(
            f"/docs/people/{employee_id}/custom/{folder_id}/upload/url",
            json_data=request.to_api_dict(),
        )
        return self._parse_response(response, Document)

    async def upload_to_custom_folder(
        self,
        employee_id: str,
        folder_id: str,
        file: BinaryIO,
        file_name: str,
        *,
        document_name: str | None = None,
    ) -> Document:
        """Upload a file to a custom folder.

        Args:
            employee_id: The employee ID.
            folder_id: The folder ID.
            file: The file to upload.
            file_name: The file name.
            document_name: Optional display name for the document.

        Returns:
            The uploaded document.
        """
        response = await self._http.post(
            f"/docs/people/{employee_id}/custom/{folder_id}",
            files={"file": (file_name, file)},
            data={"documentName": document_name} if document_name else None,
        )
        return self._parse_response(response, Document)

    async def delete_from_custom_folder(
        self,
        employee_id: str,
        folder_id: str,
        document_id: str,
    ) -> None:
        """Delete a document from a custom folder.

        Args:
            employee_id: The employee ID.
            folder_id: The folder ID.
            document_id: The document ID.
        """
        await self._http.delete(
            f"/docs/people/{employee_id}/custom/{folder_id}/{document_id}"
        )
