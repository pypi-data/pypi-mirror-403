"""Tasks API endpoints."""

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.tasks.models import Task, TasksResponse


class TasksAPI(BaseAPI):
    """API for managing tasks in Bob."""

    async def get_open_tasks(self) -> list[Task]:
        """Get all open tasks.

        Returns:
            List of open tasks.
        """
        response = await self._http.get("/tasks")
        parsed = self._parse_response(response, TasksResponse)
        return parsed.tasks

    async def get_employee_tasks(self, employee_id: str) -> list[Task]:
        """Get tasks for a specific employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of tasks for the employee.
        """
        response = await self._http.get(f"/tasks/people/{employee_id}")
        parsed = self._parse_response(response, TasksResponse)
        return parsed.tasks

    async def complete_task(self, task_id: str) -> None:
        """Mark a task as complete.

        Args:
            task_id: The task ID.
        """
        await self._http.post(f"/tasks/{task_id}/complete")
