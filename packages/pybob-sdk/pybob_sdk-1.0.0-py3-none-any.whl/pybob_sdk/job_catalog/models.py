"""Models for the Job Catalog API domain."""

from typing import Any

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


# Metadata Models
class JobProfileMetadata(BobModel):
    """Metadata for job profiles."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


class JobRoleMetadata(BobModel):
    """Metadata for job roles."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


class JobFamilyMetadata(BobModel):
    """Metadata for job families."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


class JobFamilyGroupMetadata(BobModel):
    """Metadata for job family groups."""

    fields: list[dict[str, Any]] = Field(default_factory=list)


# Job Profile Models
class JobProfile(BobModel):
    """A job profile."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    job_role_id: str | None = Field(default=None, alias="jobRoleId")
    job_role_name: str | None = Field(default=None, alias="jobRoleName")
    job_family_id: str | None = Field(default=None, alias="jobFamilyId")
    job_family_name: str | None = Field(default=None, alias="jobFamilyName")
    level: str | None = None


class JobProfileSearchRequest(BobModel):
    """Request body for searching job profiles."""

    filters: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)


# Job Role Models
class JobRole(BobModel):
    """A job role."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    job_family_id: str | None = Field(default=None, alias="jobFamilyId")
    job_family_name: str | None = Field(default=None, alias="jobFamilyName")


# Job Family Models
class JobFamily(BobModel):
    """A job family."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    job_family_group_id: str | None = Field(default=None, alias="jobFamilyGroupId")
    job_family_group_name: str | None = Field(default=None, alias="jobFamilyGroupName")


# Job Family Group Models
class JobFamilyGroup(BobModel):
    """A job family group."""

    id: str | None = None
    name: str | None = None
    description: str | None = None


# Response Models
class JobProfileSearchResponse(BobModel):
    """Response from job profile search."""

    profiles: list[JobProfile] = Field(default_factory=list)


class JobRolesResponse(BobModel):
    """Response containing job roles."""

    roles: list[JobRole] = Field(default_factory=list)


class JobFamiliesResponse(BobModel):
    """Response containing job families."""

    families: list[JobFamily] = Field(default_factory=list)


class JobFamilyGroupsResponse(BobModel):
    """Response containing job family groups."""

    groups: list[JobFamilyGroup] = Field(default_factory=list)
