"""Main Bob client for the PyBob SDK."""

from typing import Any

from pybob_sdk._core.http import HTTPClient
from pybob_sdk._core.settings import BobSettings, get_settings
from pybob_sdk.attendance.api import AttendanceAPI
from pybob_sdk.docs.api import DocsAPI
from pybob_sdk.employee_tables.api import EmployeeTablesAPI
from pybob_sdk.goals.api import GoalsAPI
from pybob_sdk.hiring.api import HiringAPI
from pybob_sdk.job_catalog.api import JobCatalogAPI
from pybob_sdk.metadata.api import MetadataAPI
from pybob_sdk.onboarding.api import OnboardingAPI
from pybob_sdk.people.api import PeopleAPI
from pybob_sdk.reports.api import ReportsAPI
from pybob_sdk.tasks.api import TasksAPI
from pybob_sdk.time_off.api import TimeOffAPI
from pybob_sdk.workforce.api import WorkforceAPI


class Bob:
    """Main client for interacting with the HiBob API.
    """

    def __init__(
        self,
        service_account_id: str | None = None,
        service_account_token: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float | None = None,
        settings: BobSettings | None = None,
    ) -> None:
        """Initialise the Bob client.

        Credentials can be provided explicitly or loaded automatically from
        environment variables. Explicit arguments take precedence over
        environment variables.

        Args:
            service_account_id: The service account ID. If not provided,
                loads from BOB_SERVICE_ACCOUNT_ID environment variable.
            service_account_token: The service account token. If not provided,
                loads from BOB_SERVICE_ACCOUNT_TOKEN environment variable.
            base_url: The base URL for the Bob API. If not provided,
                loads from BOB_BASE_URL or defaults to https://api.hibob.com/v1.
            timeout: Request timeout in seconds. If not provided,
                loads from BOB_TIMEOUT or defaults to 30.0.
            settings: Optional pre-configured BobSettings instance.

        Raises:
            ValueError: If credentials are not provided and cannot be loaded
                from environment variables.
        """
        # Load settings from environment if not provided
        if settings is None:
            settings = get_settings()

        # Use explicit arguments if provided, otherwise fall back to settings
        final_service_account_id = service_account_id or settings.service_account_id
        final_service_account_token = (
            service_account_token or settings.service_account_token
        )
        final_base_url = base_url or settings.base_url
        final_timeout = timeout if timeout is not None else settings.timeout

        # Validate credentials
        if not final_service_account_id or not final_service_account_token:
            raise ValueError(
                "Missing credentials. Provide service_account_id and "
                "service_account_token as arguments, or set BOB_SERVICE_ACCOUNT_ID "
                "and BOB_SERVICE_ACCOUNT_TOKEN environment variables."
            )

        # Create settings with validated credentials
        self._settings = BobSettings(
            service_account_id=final_service_account_id,
            service_account_token=final_service_account_token,
            base_url=final_base_url,
            timeout=final_timeout,
        )
        self._http = HTTPClient(self._settings)

        # Initialise API domains
        self._people: PeopleAPI | None = None
        self._onboarding: OnboardingAPI | None = None
        self._metadata: MetadataAPI | None = None
        self._employee_tables: EmployeeTablesAPI | None = None
        self._time_off: TimeOffAPI | None = None
        self._attendance: AttendanceAPI | None = None
        self._tasks: TasksAPI | None = None
        self._reports: ReportsAPI | None = None
        self._docs: DocsAPI | None = None
        self._goals: GoalsAPI | None = None
        self._job_catalog: JobCatalogAPI | None = None
        self._workforce: WorkforceAPI | None = None
        self._hiring: HiringAPI | None = None

    @classmethod
    def from_settings(cls, settings: BobSettings | None = None) -> "Bob":
        """Create a Bob client from settings.

        Args:
            settings: Optional pre-configured BobSettings instance.
                If not provided, loads from environment variables.

        Returns:
            A configured Bob client instance.

        Raises:
            ValueError: If credentials are not configured in settings.
        """
        if settings is None:
            settings = get_settings()

        return cls(settings=settings)

    async def __aenter__(self) -> "Bob":
        """Enter the async context manager."""
        await self._http.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the async context manager."""
        await self._http.__aexit__(exc_type, exc_val, exc_tb)

    async def close(self) -> None:
        """Close the client and release resources."""
        await self._http.close()

    @property
    def people(self) -> PeopleAPI:
        """Access the People API for managing employees.

        Returns:
            The People API instance.
        """
        if self._people is None:
            self._people = PeopleAPI(self._http)
        return self._people

    @property
    def onboarding(self) -> OnboardingAPI:
        """Access the Onboarding API for managing onboarding wizards.

        Returns:
            The Onboarding API instance.
        """
        if self._onboarding is None:
            self._onboarding = OnboardingAPI(self._http)
        return self._onboarding

    @property
    def metadata(self) -> MetadataAPI:
        """Access the Metadata API for managing fields and lists.

        Returns:
            The Metadata API instance.
        """
        if self._metadata is None:
            self._metadata = MetadataAPI(self._http)
        return self._metadata

    @property
    def employee_tables(self) -> EmployeeTablesAPI:
        """Access the Employee Tables API for work, employment, salary history, etc.

        Returns:
            The Employee Tables API instance.
        """
        if self._employee_tables is None:
            self._employee_tables = EmployeeTablesAPI(self._http)
        return self._employee_tables

    @property
    def time_off(self) -> TimeOffAPI:
        """Access the Time Off API for managing leave requests.

        Returns:
            The Time Off API instance.
        """
        if self._time_off is None:
            self._time_off = TimeOffAPI(self._http)
        return self._time_off

    @property
    def attendance(self) -> AttendanceAPI:
        """Access the Attendance API for projects and attendance tracking.

        Returns:
            The Attendance API instance.
        """
        if self._attendance is None:
            self._attendance = AttendanceAPI(self._http)
        return self._attendance

    @property
    def tasks(self) -> TasksAPI:
        """Access the Tasks API for managing tasks.

        Returns:
            The Tasks API instance.
        """
        if self._tasks is None:
            self._tasks = TasksAPI(self._http)
        return self._tasks

    @property
    def reports(self) -> ReportsAPI:
        """Access the Reports API for downloading reports.

        Returns:
            The Reports API instance.
        """
        if self._reports is None:
            self._reports = ReportsAPI(self._http)
        return self._reports

    @property
    def docs(self) -> DocsAPI:
        """Access the Documents API for managing employee documents.

        Returns:
            The Documents API instance.
        """
        if self._docs is None:
            self._docs = DocsAPI(self._http)
        return self._docs

    @property
    def goals(self) -> GoalsAPI:
        """Access the Goals API for managing goals and key results.

        Returns:
            The Goals API instance.
        """
        if self._goals is None:
            self._goals = GoalsAPI(self._http)
        return self._goals

    @property
    def job_catalog(self) -> JobCatalogAPI:
        """Access the Job Catalog API for job profiles, roles, and families.

        Returns:
            The Job Catalog API instance.
        """
        if self._job_catalog is None:
            self._job_catalog = JobCatalogAPI(self._http)
        return self._job_catalog

    @property
    def workforce(self) -> WorkforceAPI:
        """Access the Workforce Planning API for positions and budgets.

        Returns:
            The Workforce API instance.
        """
        if self._workforce is None:
            self._workforce = WorkforceAPI(self._http)
        return self._workforce

    @property
    def hiring(self) -> HiringAPI:
        """Access the Hiring API for job advertisements.

        Returns:
            The Hiring API instance.
        """
        if self._hiring is None:
            self._hiring = HiringAPI(self._http)
        return self._hiring
