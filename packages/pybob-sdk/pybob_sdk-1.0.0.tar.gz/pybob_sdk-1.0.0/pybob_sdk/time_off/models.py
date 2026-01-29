"""Models for the Time Off API domain."""

from datetime import date, datetime

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


class TimeOffRequestCreateRequest(BobModel):
    """Request body for creating a time off request."""

    employee_id: str = Field(alias="employeeId")
    policy_type: str = Field(alias="policyType")
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    hours: float | None = None
    minutes: int | None = None
    start_date_portion: str | None = Field(default=None, alias="startDatePortion")
    end_date_portion: str | None = Field(default=None, alias="endDatePortion")
    description: str | None = None
    reason_code: str | None = Field(default=None, alias="reasonCode")
    approver: str | None = None
    skip_manager_approval: bool = Field(default=False, alias="skipManagerApproval")


class TimeOffRequest(BobModel):
    """A time off request."""

    id: int | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    policy_type: str | None = Field(default=None, alias="policyType")
    policy_type_display_name: str | None = Field(
        default=None, alias="policyTypeDisplayName"
    )
    status: str | None = None
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    start_date_portion: str | None = Field(default=None, alias="startDatePortion")
    end_date_portion: str | None = Field(default=None, alias="endDatePortion")
    description: str | None = None
    reason_code: str | None = Field(default=None, alias="reasonCode")
    request_id: int | None = Field(default=None, alias="requestId")
    created_at: datetime | None = Field(default=None, alias="createdAt")


class TimeOffRequestChange(BobModel):
    """A change to a time off request."""

    change_type: str | None = Field(default=None, alias="changeType")
    changed_at: datetime | None = Field(default=None, alias="changedAt")
    request: TimeOffRequest | None = None


class OutOfOfficeEntry(BobModel):
    """An entry for someone who is out of the office."""

    employee_id: str | None = Field(default=None, alias="employeeId")
    employee_display_name: str | None = Field(default=None, alias="employeeDisplayName")
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    policy_type: str | None = Field(default=None, alias="policyType")
    policy_type_display_name: str | None = Field(
        default=None, alias="policyTypeDisplayName"
    )
    start_portion: str | None = Field(default=None, alias="startPortion")
    end_portion: str | None = Field(default=None, alias="endPortion")


class ReasonCode(BobModel):
    """A reason code for a policy type."""

    id: str | None = None
    code: str | None = None
    name: str | None = None
    description: str | None = None


class PolicyType(BobModel):
    """A time off policy type."""

    name: str | None = None
    policy_type: str | None = Field(default=None, alias="policyType")


class Policy(BobModel):
    """A time off policy."""

    name: str | None = None
    policy_type: str | None = Field(default=None, alias="policyType")


class PolicyDetails(BobModel):
    """Details of a time off policy type."""

    name: str | None = None
    policy_type: str | None = Field(default=None, alias="policyType")
    allow_request_hours: bool | None = Field(default=None, alias="allowRequestHours")
    unit: str | None = None
    negative_balance_limit: float | None = Field(
        default=None, alias="negativeBalanceLimit"
    )


class TimeOffBalance(BobModel):
    """Time off balance for an employee."""

    employee_id: str | None = Field(default=None, alias="employeeId")
    policy_type: str | None = Field(default=None, alias="policyType")
    balance: float | None = None
    used: float | None = None
    pending: float | None = None
    available: float | None = None
    unit: str | None = None


class BalanceAdjustmentCreateRequest(BobModel):
    """Request body for creating a balance adjustment."""

    employee_id: str = Field(alias="employeeId")
    policy_type: str = Field(alias="policyType")
    amount: float
    effective_date: date = Field(alias="effectiveDate")
    reason: str | None = None
    adjustment_type: str | None = Field(default=None, alias="adjustmentType")


class BalanceAdjustment(BobModel):
    """A balance adjustment."""

    id: str | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    policy_type: str | None = Field(default=None, alias="policyType")
    amount: float | None = None
    effective_date: date | None = Field(default=None, alias="effectiveDate")
    reason: str | None = None


class OutOfOfficeResponse(BobModel):
    """Response containing out of office entries."""

    outs: list[OutOfOfficeEntry] = Field(default_factory=list)


class TimeOffChangesResponse(BobModel):
    """Response containing time off request changes."""

    changes: list[TimeOffRequestChange] = Field(default_factory=list)


class ReasonCodesResponse(BobModel):
    """Response containing reason codes."""

    reason_codes: list[ReasonCode] = Field(default_factory=list, alias="reasonCodes")


class PolicyTypesResponse(BobModel):
    """Response containing policy type names.

    The API returns a list of strings directly, not wrapped in objects.
    """

    policy_types: list[str] = Field(default_factory=list, alias="policyTypes")


class PoliciesResponse(BobModel):
    """Response containing policies."""

    policies: list[Policy] = Field(default_factory=list)
