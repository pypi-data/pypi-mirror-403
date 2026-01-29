"""Hiring API endpoints."""

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.hiring.models import (
    JobAd,
    JobAdSearchRequest,
    JobAdsResponse,
)


class HiringAPI(BaseAPI):
    """API for managing hiring/job ads in Bob."""

    async def get_active_job_ads(
        self,
        request: JobAdSearchRequest | None = None,
    ) -> list[JobAd]:
        """Get all active job ads from the career page.

        Args:
            request: Optional search request.

        Returns:
            List of active job ads.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post("/hiring/job-ads", json_data=json_data)
        parsed = self._parse_response(response, JobAdsResponse)
        return parsed.jobs

    async def get_job_ad(self, job_id: str) -> JobAd:
        """Get details of a single job ad.

        Args:
            job_id: The job ad ID.

        Returns:
            The job ad details.
        """
        response = await self._http.get(f"/hiring/job-ads/{job_id}")
        return self._parse_response(response, JobAd)
