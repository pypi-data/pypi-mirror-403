"""Models for the Employee Tables API domain."""

from datetime import date
from typing import Any

from pydantic import Field

from pybob_sdk._core.base_model import BobModel


# Work History Models
class WorkEntry(BobModel):
    """A work history entry for an employee."""

    id: int | None = None
    effective_date: date | None = Field(default=None, alias="effectiveDate")
    title: str | None = None
    department: str | None = None
    site: str | None = None
    site_id: int | None = Field(default=None, alias="siteId")
    reports_to_id: str | None = Field(default=None, alias="reportsToId")
    reports_to: dict[str, Any] | None = Field(default=None, alias="reportsTo")


class WorkEntryCreateRequest(BobModel):
    """Request body for creating a work history entry."""

    effective_date: date = Field(alias="effectiveDate")
    title: str | None = None
    department: str | None = None
    site: str | None = None
    site_id: int | None = Field(default=None, alias="siteId")
    reports_to_id: str | None = Field(default=None, alias="reportsToId")
    reason: str | None = None


class WorkEntryUpdateRequest(BobModel):
    """Request body for updating a work history entry."""

    effective_date: date | None = Field(default=None, alias="effectiveDate")
    title: str | None = None
    department: str | None = None
    site: str | None = None
    site_id: int | None = Field(default=None, alias="siteId")
    reports_to_id: str | None = Field(default=None, alias="reportsToId")
    reason: str | None = None


class WorkHistoryResponse(BobModel):
    """Response containing work history entries."""

    values: list[WorkEntry] = Field(default_factory=list)


# Employment History Models
class WorkingPatternDays(BobModel):
    """Working pattern days configuration."""

    monday: float = 0
    tuesday: float = 0
    wednesday: float = 0
    thursday: float = 0
    friday: float = 0
    saturday: float = 0
    sunday: float = 0


class WorkingPattern(BobModel):
    """Working pattern configuration."""

    days: WorkingPatternDays | None = None


class EmploymentEntry(BobModel):
    """An employment history entry for an employee."""

    id: int | None = None
    effective_date: date | None = Field(default=None, alias="effectiveDate")
    contract: str | None = None
    type: str | None = None
    fte_percent: float | None = Field(default=None, alias="ftePercent")
    working_pattern: WorkingPattern | None = Field(default=None, alias="workingPattern")
    weekly_hours: float | None = Field(default=None, alias="weeklyHours")
    actual_start_date: date | None = Field(default=None, alias="actualStartDate")
    salary_pay_type: str | None = Field(default=None, alias="salaryPayType")


class EmploymentEntryCreateRequest(BobModel):
    """Request body for creating an employment entry."""

    effective_date: date = Field(alias="effectiveDate")
    contract: str | None = None
    type: str | None = None
    fte_percent: float | None = Field(default=None, alias="ftePercent")
    working_pattern: dict[str, Any] | None = Field(default=None, alias="workingPattern")
    weekly_hours: float | None = Field(default=None, alias="weeklyHours")
    reason: str | None = None


class EmploymentEntryUpdateRequest(BobModel):
    """Request body for updating an employment entry."""

    effective_date: date | None = Field(default=None, alias="effectiveDate")
    contract: str | None = None
    type: str | None = None
    fte_percent: float | None = Field(default=None, alias="ftePercent")
    working_pattern: dict[str, Any] | None = Field(default=None, alias="workingPattern")
    weekly_hours: float | None = Field(default=None, alias="weeklyHours")
    reason: str | None = None


class EmploymentHistoryResponse(BobModel):
    """Response containing employment history entries."""

    values: list[EmploymentEntry] = Field(default_factory=list)


# Lifecycle Models
class LifecycleEntry(BobModel):
    """A lifecycle status entry for an employee."""

    id: int | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    effective_date: date | None = Field(default=None, alias="effectiveDate")
    status: str | None = None
    status_type: str | None = Field(default=None, alias="statusType")
    second_level_type: str | None = Field(default=None, alias="secondLevelType")


class LifecycleHistoryResponse(BobModel):
    """Response containing lifecycle history entries."""

    values: list[LifecycleEntry] = Field(default_factory=list)


# Salary Models
class SalaryEntry(BobModel):
    """A salary entry for an employee."""

    id: int | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    effective_date: date | None = Field(default=None, alias="effectiveDate")
    base_salary: float | None = Field(default=None, alias="baseSalary")
    pay_period: str | None = Field(default=None, alias="payPeriod")
    pay_frequency: str | None = Field(default=None, alias="payFrequency")
    currency: str | None = None


class SalaryEntryCreateRequest(BobModel):
    """Request body for creating a salary entry."""

    effective_date: date = Field(alias="effectiveDate")
    base_salary: float = Field(alias="baseSalary")
    pay_period: str = Field(alias="payPeriod")
    pay_frequency: str | None = Field(default=None, alias="payFrequency")
    currency: str | None = None
    reason: str | None = None


class SalaryHistoryResponse(BobModel):
    """Response containing salary history entries."""

    values: list[SalaryEntry] = Field(default_factory=list)


# Payroll Models
class PayrollEntry(BobModel):
    """A payroll history entry."""

    id: int | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    effective_date: date | None = Field(default=None, alias="effectiveDate")
    base_salary: float | None = Field(default=None, alias="baseSalary")
    pay_period: str | None = Field(default=None, alias="payPeriod")
    currency: str | None = None


class PayrollHistoryResponse(BobModel):
    """Response containing payroll history."""

    employees: list[dict[str, Any]] = Field(default_factory=list)


# Equity Grant Models
class EquityGrant(BobModel):
    """An equity grant for an employee."""

    id: int | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    grant_date: date | None = Field(default=None, alias="grantDate")
    equity_type: str | None = Field(default=None, alias="equityType")
    quantity: float | None = None
    exercise_price: float | None = Field(default=None, alias="exercisePrice")
    currency: str | None = None
    vesting_commencement_date: date | None = Field(
        default=None, alias="vestingCommencementDate"
    )
    grant_type: str | None = Field(default=None, alias="grantType")
    vesting_term: int | None = Field(default=None, alias="vestingTerm")
    grant_number: str | None = Field(default=None, alias="grantNumber")
    reason: str | None = None
    vesting_schedule: str | None = Field(default=None, alias="vestingSchedule")


class EquityGrantCreateRequest(BobModel):
    """Request body for creating an equity grant."""

    grant_date: date = Field(alias="grantDate")
    equity_type: str | None = Field(default=None, alias="equityType")
    quantity: float
    exercise_price: float | None = Field(default=None, alias="exercisePrice")
    currency: str | None = None
    vesting_commencement_date: date | None = Field(
        default=None, alias="vestingCommencementDate"
    )
    grant_type: str | None = Field(default=None, alias="grantType")
    vesting_term: int | None = Field(default=None, alias="vestingTerm")
    grant_number: str | None = Field(default=None, alias="grantNumber")
    reason: str | None = None


class EquityGrantUpdateRequest(BobModel):
    """Request body for updating an equity grant."""

    grant_date: date | None = Field(default=None, alias="grantDate")
    equity_type: str | None = Field(default=None, alias="equityType")
    quantity: float | None = None
    exercise_price: float | None = Field(default=None, alias="exercisePrice")
    currency: str | None = None
    vesting_commencement_date: date | None = Field(
        default=None, alias="vestingCommencementDate"
    )
    grant_type: str | None = Field(default=None, alias="grantType")
    vesting_term: int | None = Field(default=None, alias="vestingTerm")
    grant_number: str | None = Field(default=None, alias="grantNumber")
    reason: str | None = None


class EquityHistoryResponse(BobModel):
    """Response containing equity grants."""

    values: list[EquityGrant] = Field(default_factory=list)


# Variable Payment Models
class VariablePayment(BobModel):
    """A variable payment for an employee."""

    id: int | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    payment_date: date | None = Field(default=None, alias="paymentDate")
    amount: float | None = None
    currency: str | None = None
    payment_type: str | None = Field(default=None, alias="paymentType")
    reason: str | None = None
    compounding_percent: float | None = Field(default=None, alias="compoundingPercent")


class VariablePaymentCreateRequest(BobModel):
    """Request body for creating a variable payment."""

    payment_date: date = Field(alias="paymentDate")
    amount: float
    currency: str | None = None
    payment_type: str | None = Field(default=None, alias="paymentType")
    reason: str | None = None


class VariablePaymentsResponse(BobModel):
    """Response containing variable payments."""

    values: list[VariablePayment] = Field(default_factory=list)


# Training Models
class TrainingRecord(BobModel):
    """A training record for an employee."""

    id: int | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    name: str | None = None
    description: str | None = None
    status: str | None = None
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    cost: float | None = None
    currency: str | None = None
    frequency: str | None = None


class TrainingRecordCreateRequest(BobModel):
    """Request body for creating a training record."""

    name: str
    description: str | None = None
    status: str | None = None
    start_date: date | None = Field(default=None, alias="startDate")
    end_date: date | None = Field(default=None, alias="endDate")
    cost: float | None = None
    currency: str | None = None
    frequency: str | None = None


class TrainingHistoryResponse(BobModel):
    """Response containing training records."""

    values: list[TrainingRecord] = Field(default_factory=list)


# Bank Account Models
class BankAccount(BobModel):
    """A bank account for an employee."""

    id: int | None = None
    employee_id: str | None = Field(default=None, alias="employeeId")
    bank_name: str | None = Field(default=None, alias="bankName")
    account_number: str | None = Field(default=None, alias="accountNumber")
    routing_number: str | None = Field(default=None, alias="routingNumber")
    account_type: str | None = Field(default=None, alias="accountType")
    iban: str | None = None
    swift: str | None = None
    bank_country: str | None = Field(default=None, alias="bankCountry")


class BankAccountCreateRequest(BobModel):
    """Request body for creating a bank account."""

    bank_name: str = Field(alias="bankName")
    account_number: str | None = Field(default=None, alias="accountNumber")
    routing_number: str | None = Field(default=None, alias="routingNumber")
    account_type: str | None = Field(default=None, alias="accountType")
    iban: str | None = None
    swift: str | None = None
    bank_country: str | None = Field(default=None, alias="bankCountry")


class BankAccountUpdateRequest(BobModel):
    """Request body for updating a bank account."""

    bank_name: str | None = Field(default=None, alias="bankName")
    account_number: str | None = Field(default=None, alias="accountNumber")
    routing_number: str | None = Field(default=None, alias="routingNumber")
    account_type: str | None = Field(default=None, alias="accountType")
    iban: str | None = None
    swift: str | None = None
    bank_country: str | None = Field(default=None, alias="bankCountry")


class BankAccountsResponse(BobModel):
    """Response containing bank accounts."""

    values: list[BankAccount] = Field(default_factory=list)


# Actual Payments Models
class ActualPaymentSearchRequest(BobModel):
    """Request body for searching actual payments."""

    employee_ids: list[str] | None = Field(default=None, alias="employeeIds")
    from_date: date | None = Field(default=None, alias="fromDate")
    to_date: date | None = Field(default=None, alias="toDate")
