"""People API domain."""

from pybob_sdk.people.api import PeopleAPI
from pybob_sdk.people.models import (
    Avatar,
    Employee,
    EmployeeCreateRequest,
    EmployeeSearchRequest,
    EmployeeSearchResponse,
    EmployeeUpdateRequest,
    PublicProfile,
    SearchFilter,
    TerminateRequest,
)

__all__ = [
    "Avatar",
    "Employee",
    "EmployeeCreateRequest",
    "EmployeeSearchRequest",
    "EmployeeSearchResponse",
    "EmployeeUpdateRequest",
    "PeopleAPI",
    "PublicProfile",
    "SearchFilter",
    "TerminateRequest",
]
