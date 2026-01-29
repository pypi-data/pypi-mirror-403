"""Models for the Hiring API domain."""

from datetime import date
from typing import Any

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


class JobAdLocation(BobModel):
    """A location for a job ad."""

    city: str | None = None
    country: str | None = None
    state: str | None = None
    address: str | None = None


class JobAd(BobModel):
    """A job advertisement."""

    id: str | None = None
    title: str | None = None
    description: str | None = None
    department: str | None = None
    site: str | None = None
    location: JobAdLocation | None = None
    employment_type: str | None = Field(default=None, alias="employmentType")
    status: str | None = None
    posted_date: date | None = Field(default=None, alias="postedDate")
    closing_date: date | None = Field(default=None, alias="closingDate")
    apply_url: str | None = Field(default=None, alias="applyUrl")
    remote: bool = False


class JobAdSearchRequest(BobModel):
    """Request body for searching job ads."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


class JobAdsResponse(BobModel):
    """Response containing job ads."""

    jobs: list[JobAd] = Field(default_factory=list)
