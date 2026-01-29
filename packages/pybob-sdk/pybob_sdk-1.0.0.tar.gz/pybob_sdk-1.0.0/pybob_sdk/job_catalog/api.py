"""Job Catalog API endpoints."""

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.job_catalog.models import (
    JobFamiliesResponse,
    JobFamily,
    JobFamilyGroup,
    JobFamilyGroupMetadata,
    JobFamilyGroupsResponse,
    JobFamilyMetadata,
    JobProfile,
    JobProfileMetadata,
    JobProfileSearchRequest,
    JobProfileSearchResponse,
    JobRole,
    JobRoleMetadata,
    JobRolesResponse,
)


class JobCatalogAPI(BaseAPI):
    """API for managing job catalogs in Bob."""

    # Metadata Methods
    async def get_profile_metadata(self) -> JobProfileMetadata:
        """Get job profile metadata.

        Returns:
            Job profile metadata.
        """
        response = await self._http.get("/job-catalog/profiles/metadata")
        return self._parse_response(response, JobProfileMetadata)

    async def get_role_metadata(self) -> JobRoleMetadata:
        """Get job role metadata.

        Returns:
            Job role metadata.
        """
        response = await self._http.get("/job-catalog/roles/metadata")
        return self._parse_response(response, JobRoleMetadata)

    async def get_family_metadata(self) -> JobFamilyMetadata:
        """Get job family metadata.

        Returns:
            Job family metadata.
        """
        response = await self._http.get("/job-catalog/families/metadata")
        return self._parse_response(response, JobFamilyMetadata)

    async def get_family_group_metadata(self) -> JobFamilyGroupMetadata:
        """Get job family group metadata.

        Returns:
            Job family group metadata.
        """
        response = await self._http.get("/job-catalog/family-groups/metadata")
        return self._parse_response(response, JobFamilyGroupMetadata)

    # Job Profile Methods
    async def search_profiles(
        self,
        request: JobProfileSearchRequest | None = None,
    ) -> list[JobProfile]:
        """Search job profiles.

        Args:
            request: The search request.

        Returns:
            List of matching job profiles.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post(
            "/job-catalog/profiles/search",
            json_data=json_data,
        )
        parsed = self._parse_response(response, JobProfileSearchResponse)
        return parsed.profiles

    # Job Role Methods
    async def get_roles(self) -> list[JobRole]:
        """Get all job roles.

        Returns:
            List of job roles.
        """
        response = await self._http.get("/job-catalog/roles")

        if response is None:
            return []

        parsed = self._parse_response(response, JobRolesResponse)
        return parsed.roles

    # Job Family Methods
    async def get_families(self) -> list[JobFamily]:
        """Get all job families.

        Returns:
            List of job families.
        """
        response = await self._http.get("/job-catalog/families")

        if response is None:
            return []

        parsed = self._parse_response(response, JobFamiliesResponse)
        return parsed.families

    # Job Family Group Methods
    async def get_family_groups(self) -> list[JobFamilyGroup]:
        """Get all job family groups.

        Returns:
            List of job family groups.
        """
        response = await self._http.get("/job-catalog/family-groups")

        if response is None:
            return []

        parsed = self._parse_response(response, JobFamilyGroupsResponse)
        return parsed.groups
