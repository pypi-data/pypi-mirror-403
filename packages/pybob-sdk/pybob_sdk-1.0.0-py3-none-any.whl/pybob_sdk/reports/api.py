"""Reports API endpoints."""

from typing import Any

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.reports.models import Report, ReportDownloadUrl, ReportsResponse


class ReportsAPI(BaseAPI):
    """API for managing reports in Bob."""

    async def get_reports(self) -> list[Report]:
        """Get all company reports.

        Returns:
            List of reports.
        """
        response = await self._http.get("/company/reports")
        parsed = self._parse_response(response, ReportsResponse)
        return parsed.reports

    async def download_report_by_id(self, report_id: str) -> dict[str, Any]:
        """Download a report by ID.

        Args:
            report_id: The report ID.

        Returns:
            The report data.
        """
        response = await self._http.get(f"/company/reports/{report_id}/download")
        if isinstance(response, dict):
            return response
        return {}

    async def get_report_download_url(self, report_id: str) -> ReportDownloadUrl:
        """Get the download URL for a report (for polling).

        Args:
            report_id: The report ID.

        Returns:
            The download URL information.
        """
        response = await self._http.get(f"/company/reports/{report_id}/download-async")
        return self._parse_response(response, ReportDownloadUrl)

    async def download_report_by_name(self, report_name: str) -> dict[str, Any]:
        """Download a report by name.

        Args:
            report_name: The report name.

        Returns:
            The report data.
        """
        response = await self._http.get(f"/company/reports/download/{report_name}")
        if isinstance(response, dict):
            return response
        return {}
