"""Attendance API endpoints."""

from datetime import date
from typing import Any

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.attendance.models import (
    AttendanceBreakdown,
    AttendanceBreakdownRequest,
    AttendanceBreakdownResponse,
    AttendanceImportRequest,
    AttendanceSummary,
    AttendanceSummaryRequest,
    AttendanceSummaryResponse,
    Project,
    ProjectClient,
    ProjectClientMetadata,
    ProjectClientSearchResponse,
    ProjectCreateRequest,
    ProjectMetadata,
    ProjectSearchRequest,
    ProjectSearchResponse,
    ProjectTask,
    ProjectTaskCreateRequest,
    ProjectTaskMetadata,
    ProjectTaskSearchResponse,
    ProjectTaskUpdateRequest,
    ProjectUpdateRequest,
)


class AttendanceAPI(BaseAPI):
    """API for managing attendance and projects in Bob."""

    # Project Methods
    async def get_project_metadata(self) -> list[ProjectMetadata]:
        """Get project metadata.

        Returns:
            List of project field metadata.
        """
        response = await self._http.get("/attendance/projects/metadata")
        if response is None:
            return []
        return self._parse_response_list(response, ProjectMetadata, key="fields")

    async def search_projects(
        self,
        request: ProjectSearchRequest | None = None,
    ) -> list[Project]:
        """Search projects.

        Args:
            request: The search request.

        Returns:
            List of matching projects.
        """
        json_data = request.to_api_dict() if request else {}
        response = await self._http.post(
            "/attendance/projects/search",
            json_data=json_data,
        )
        parsed = self._parse_response(response, ProjectSearchResponse)
        return parsed.projects

    async def create_projects(
        self,
        projects: list[ProjectCreateRequest],
    ) -> list[Project]:
        """Create one or more projects.

        Args:
            projects: List of project data.

        Returns:
            List of created projects.
        """
        response = await self._http.post(
            "/attendance/projects",
            json_data={"projects": [p.to_api_dict() for p in projects]},
        )
        return self._parse_response_list(response, Project, key="projects")

    async def update_project(
        self,
        project_id: str,
        project: ProjectUpdateRequest,
    ) -> None:
        """Update a project.

        Args:
            project_id: The project ID.
            project: The updated project data.
        """
        await self._http.patch(
            f"/attendance/projects/{project_id}",
            json_data=project.to_api_dict(),
        )

    async def archive_project(self, project_id: str) -> None:
        """Archive a project.

        Args:
            project_id: The project ID.
        """
        await self._http.patch(f"/attendance/projects/{project_id}/archive")

    async def restore_project(self, project_id: str) -> None:
        """Restore an archived project.

        Args:
            project_id: The project ID.
        """
        await self._http.patch(f"/attendance/projects/{project_id}/restore")

    # Project Client Methods
    async def get_client_metadata(self) -> ProjectClientMetadata:
        """Get project client metadata.

        Returns:
            Project client metadata.
        """
        response = await self._http.get("/attendance/projects/clients/metadata")
        return self._parse_response(response, ProjectClientMetadata)

    async def search_clients(
        self,
        filters: list[dict[str, Any]] | None = None,
    ) -> list[ProjectClient]:
        """Search project clients.

        Args:
            filters: Optional filters.

        Returns:
            List of matching clients.
        """
        response = await self._http.post(
            "/attendance/projects/clients/search",
            json_data={"filters": filters or []},
        )
        parsed = self._parse_response(response, ProjectClientSearchResponse)
        return parsed.clients

    # Project Task Methods
    async def get_task_metadata(self) -> ProjectTaskMetadata:
        """Get project task metadata.

        Returns:
            Project task metadata.
        """
        response = await self._http.get("/attendance/projects/tasks/metadata")
        return self._parse_response(response, ProjectTaskMetadata)

    async def search_tasks(
        self,
        filters: list[dict[str, Any]] | None = None,
    ) -> list[ProjectTask]:
        """Search project tasks.

        Args:
            filters: Optional filters.

        Returns:
            List of matching tasks.
        """
        response = await self._http.post(
            "/attendance/projects/tasks/search",
            json_data={"filters": filters or []},
        )
        parsed = self._parse_response(response, ProjectTaskSearchResponse)
        return parsed.tasks

    async def create_tasks(
        self,
        tasks: list[ProjectTaskCreateRequest],
    ) -> list[ProjectTask]:
        """Create one or more project tasks.

        Args:
            tasks: List of task data.

        Returns:
            List of created tasks.
        """
        response = await self._http.post(
            "/attendance/projects/tasks",
            json_data={"tasks": [t.to_api_dict() for t in tasks]},
        )
        return self._parse_response_list(response, ProjectTask, key="tasks")

    async def update_task(
        self,
        task_id: str,
        task: ProjectTaskUpdateRequest,
    ) -> None:
        """Update a project task.

        Args:
            task_id: The task ID.
            task: The updated task data.
        """
        await self._http.put(
            f"/attendance/projects/tasks/{task_id}",
            json_data=task.to_api_dict(),
        )

    async def archive_task(self, task_id: str) -> None:
        """Archive a project task.

        Args:
            task_id: The task ID.
        """
        await self._http.patch(f"/attendance/projects/tasks/{task_id}/archive")

    async def restore_task(self, task_id: str) -> None:
        """Restore an archived project task.

        Args:
            task_id: The task ID.
        """
        await self._http.patch(f"/attendance/projects/tasks/{task_id}/restore")

    # Attendance Methods
    async def import_attendance(
        self,
        request: AttendanceImportRequest,
    ) -> None:
        """Import attendance data.

        Args:
            request: The import request.
        """
        await self._http.post(
            "/attendance/import",
            json_data=request.to_api_dict(),
        )

    async def get_summaries(
        self,
        employee_ids: list[str],
        from_date: date,
        to_date: date,
    ) -> list[AttendanceSummary]:
        """Fetch attendance summaries.

        Args:
            employee_ids: List of employee IDs.
            from_date: Start date.
            to_date: End date.

        Returns:
            List of attendance summaries.
        """
        request = AttendanceSummaryRequest(
            employee_ids=employee_ids,
            from_date=from_date,
            to_date=to_date,
        )
        response = await self._http.post(
            "/attendance/summary",
            json_data=request.to_api_dict(),
        )
        parsed = self._parse_response(response, AttendanceSummaryResponse)
        return parsed.summaries

    async def get_daily_breakdown(
        self,
        employee_ids: list[str],
        from_date: date,
        to_date: date,
    ) -> list[AttendanceBreakdown]:
        """Fetch daily attendance breakdown.

        Args:
            employee_ids: List of employee IDs.
            from_date: Start date.
            to_date: End date.

        Returns:
            List of attendance breakdowns.
        """
        request = AttendanceBreakdownRequest(
            employee_ids=employee_ids,
            from_date=from_date,
            to_date=to_date,
        )
        response = await self._http.post(
            "/attendance/breakdown",
            json_data=request.to_api_dict(),
        )
        parsed = self._parse_response(response, AttendanceBreakdownResponse)
        return parsed.employees
