"""Models for the Reports API domain."""

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


class Report(BobModel):
    """A report in Bob."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    report_type: str | None = Field(default=None, alias="reportType")


class ReportDownloadUrl(BobModel):
    """A download URL for a report."""

    url: str | None = None
    expires_at: str | None = Field(default=None, alias="expiresAt")


class ReportsResponse(BobModel):
    """Response containing reports."""

    reports: list[Report] = Field(default_factory=list)
