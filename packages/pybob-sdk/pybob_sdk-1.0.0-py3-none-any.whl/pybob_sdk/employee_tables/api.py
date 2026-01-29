"""Employee Tables API endpoints."""

from typing import Any

from pybob_sdk._core.base_api import BaseAPI
from pybob_sdk.employee_tables.models import (
    ActualPaymentSearchRequest,
    BankAccount,
    BankAccountCreateRequest,
    BankAccountsResponse,
    BankAccountUpdateRequest,
    EmploymentEntry,
    EmploymentEntryCreateRequest,
    EmploymentEntryUpdateRequest,
    EmploymentHistoryResponse,
    EquityGrant,
    EquityGrantCreateRequest,
    EquityGrantUpdateRequest,
    EquityHistoryResponse,
    LifecycleEntry,
    LifecycleHistoryResponse,
    PayrollHistoryResponse,
    SalaryEntry,
    SalaryEntryCreateRequest,
    SalaryHistoryResponse,
    TrainingHistoryResponse,
    TrainingRecord,
    TrainingRecordCreateRequest,
    VariablePayment,
    VariablePaymentCreateRequest,
    VariablePaymentsResponse,
    WorkEntry,
    WorkEntryCreateRequest,
    WorkEntryUpdateRequest,
    WorkHistoryResponse,
)


class EmployeeTablesAPI(BaseAPI):
    """API for managing employee table data in Bob."""

    # Work History Methods
    async def list_work_history(
        self,
        employee_ids: list[str] | None = None,
    ) -> list[WorkEntry]:
        """List work history for employees.

        Args:
            employee_ids: Optional list of employee IDs to filter by.

        Returns:
            List of work history entries.
        """
        params = {}
        if employee_ids:
            params["employeeId"] = ",".join(employee_ids)

        response = await self._http.get("/people/work", params=params or None)
        parsed = self._parse_response(response, WorkHistoryResponse)
        return parsed.values

    async def get_work_history(self, employee_id: str) -> list[WorkEntry]:
        """Get work history for a specific employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of work history entries.
        """
        response = await self._http.get(f"/people/{employee_id}/work")
        parsed = self._parse_response(response, WorkHistoryResponse)
        return parsed.values

    async def create_work_entry(
        self,
        employee_id: str,
        entry: WorkEntryCreateRequest,
    ) -> WorkEntry:
        """Create a work history entry for an employee.

        Args:
            employee_id: The employee ID.
            entry: The work entry data.

        Returns:
            The created work entry.
        """
        response = await self._http.post(
            f"/people/{employee_id}/work",
            json_data=entry.to_api_dict(),
        )
        return self._parse_response(response, WorkEntry)

    async def update_work_entry(
        self,
        employee_id: str,
        entry_id: int,
        entry: WorkEntryUpdateRequest,
    ) -> None:
        """Update a work history entry.

        Args:
            employee_id: The employee ID.
            entry_id: The work entry ID.
            entry: The updated work entry data.
        """
        await self._http.put(
            f"/people/{employee_id}/work/{entry_id}",
            json_data=entry.to_api_dict(),
        )

    async def delete_work_entry(
        self,
        employee_id: str,
        entry_id: int,
    ) -> None:
        """Delete a work history entry.

        Args:
            employee_id: The employee ID.
            entry_id: The work entry ID.
        """
        await self._http.delete(f"/people/{employee_id}/work/{entry_id}")

    # Employment History Methods
    async def list_employment_history(
        self,
        employee_ids: list[str] | None = None,
    ) -> list[EmploymentEntry]:
        """List employment history for employees.

        Args:
            employee_ids: Optional list of employee IDs to filter by.

        Returns:
            List of employment history entries.
        """
        params = {}
        if employee_ids:
            params["employeeId"] = ",".join(employee_ids)

        response = await self._http.get("/people/employment", params=params or None)
        parsed = self._parse_response(response, EmploymentHistoryResponse)
        return parsed.values

    async def get_employment_history(self, employee_id: str) -> list[EmploymentEntry]:
        """Get employment history for a specific employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of employment history entries.
        """
        response = await self._http.get(f"/people/{employee_id}/employment")
        parsed = self._parse_response(response, EmploymentHistoryResponse)
        return parsed.values

    async def create_employment_entry(
        self,
        employee_id: str,
        entry: EmploymentEntryCreateRequest,
    ) -> EmploymentEntry:
        """Create an employment history entry for an employee.

        Args:
            employee_id: The employee ID.
            entry: The employment entry data.

        Returns:
            The created employment entry.
        """
        response = await self._http.post(
            f"/people/{employee_id}/employment",
            json_data=entry.to_api_dict(),
        )
        return self._parse_response(response, EmploymentEntry)

    async def update_employment_entry(
        self,
        employee_id: str,
        entry_id: int,
        entry: EmploymentEntryUpdateRequest,
    ) -> None:
        """Update an employment history entry.

        Args:
            employee_id: The employee ID.
            entry_id: The employment entry ID.
            entry: The updated employment entry data.
        """
        await self._http.put(
            f"/people/{employee_id}/employment/{entry_id}",
            json_data=entry.to_api_dict(),
        )

    async def delete_employment_entry(
        self,
        employee_id: str,
        entry_id: int,
    ) -> None:
        """Delete an employment history entry.

        Args:
            employee_id: The employee ID.
            entry_id: The employment entry ID.
        """
        await self._http.delete(f"/people/{employee_id}/employment/{entry_id}")

    # Lifecycle History Methods
    async def list_lifecycle_history(
        self,
        employee_ids: list[str] | None = None,
    ) -> list[LifecycleEntry]:
        """List lifecycle history for employees.

        Args:
            employee_ids: Optional list of employee IDs to filter by.

        Returns:
            List of lifecycle history entries.
        """
        params = {}
        if employee_ids:
            params["employeeId"] = ",".join(employee_ids)

        response = await self._http.get("/people/lifecycle", params=params or None)
        parsed = self._parse_response(response, LifecycleHistoryResponse)
        return parsed.values

    async def get_lifecycle_history(self, employee_id: str) -> list[LifecycleEntry]:
        """Get lifecycle history for a specific employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of lifecycle history entries.
        """
        response = await self._http.get(f"/people/{employee_id}/lifecycle")
        parsed = self._parse_response(response, LifecycleHistoryResponse)
        return parsed.values

    # Salary History Methods
    async def list_salary_history(
        self,
        employee_ids: list[str] | None = None,
    ) -> list[SalaryEntry]:
        """List salary history for employees.

        Args:
            employee_ids: Optional list of employee IDs to filter by.

        Returns:
            List of salary history entries.
        """
        params = {}
        if employee_ids:
            params["employeeId"] = ",".join(employee_ids)

        response = await self._http.get("/people/salaries", params=params or None)
        parsed = self._parse_response(response, SalaryHistoryResponse)
        return parsed.values

    async def get_salary_history(self, employee_id: str) -> list[SalaryEntry]:
        """Get salary history for a specific employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of salary history entries.
        """
        response = await self._http.get(f"/people/{employee_id}/salaries")
        parsed = self._parse_response(response, SalaryHistoryResponse)
        return parsed.values

    async def create_salary_entry(
        self,
        employee_id: str,
        entry: SalaryEntryCreateRequest,
    ) -> SalaryEntry:
        """Create a salary entry for an employee.

        Args:
            employee_id: The employee ID.
            entry: The salary entry data.

        Returns:
            The created salary entry.
        """
        response = await self._http.post(
            f"/people/{employee_id}/salaries",
            json_data=entry.to_api_dict(),
        )
        return self._parse_response(response, SalaryEntry)

    async def delete_salary_entry(
        self,
        employee_id: str,
        entry_id: int,
    ) -> None:
        """Delete a salary entry.

        Args:
            employee_id: The employee ID.
            entry_id: The salary entry ID.
        """
        await self._http.delete(f"/people/{employee_id}/salaries/{entry_id}")

    # Payroll History Methods
    async def get_payroll_history(
        self,
        employee_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get payroll tables history.

        Args:
            employee_ids: Optional list of employee IDs to filter by.

        Returns:
            Payroll history data.
        """
        params = {}
        if employee_ids:
            params["employeeId"] = ",".join(employee_ids)

        response = await self._http.get("/payroll/history", params=params or None)
        parsed = self._parse_response(response, PayrollHistoryResponse)
        return {"employees": parsed.employees}

    async def search_actual_payments(
        self,
        request: ActualPaymentSearchRequest,
    ) -> list[dict[str, Any]]:
        """Search for actual payments.

        Args:
            request: The search request.

        Returns:
            List of actual payments.
        """
        response = await self._http.post(
            "/payroll/actual-payments",
            json_data=request.to_api_dict(),
        )
        if isinstance(response, list):
            return response
        return []

    # Equity Grant Methods
    async def get_equity_grants(self, employee_id: str) -> list[EquityGrant]:
        """Get equity grants for an employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of equity grants.
        """
        response = await self._http.get(f"/people/{employee_id}/equities")
        parsed = self._parse_response(response, EquityHistoryResponse)
        return parsed.values

    async def create_equity_grant(
        self,
        employee_id: str,
        grant: EquityGrantCreateRequest,
    ) -> EquityGrant:
        """Create an equity grant for an employee.

        Args:
            employee_id: The employee ID.
            grant: The equity grant data.

        Returns:
            The created equity grant.
        """
        response = await self._http.post(
            f"/people/{employee_id}/equities",
            json_data=grant.to_api_dict(),
        )
        return self._parse_response(response, EquityGrant)

    async def update_equity_grant(
        self,
        employee_id: str,
        grant_id: int,
        grant: EquityGrantUpdateRequest,
    ) -> None:
        """Update an equity grant.

        Args:
            employee_id: The employee ID.
            grant_id: The equity grant ID.
            grant: The updated equity grant data.
        """
        await self._http.put(
            f"/people/{employee_id}/equities/{grant_id}",
            json_data=grant.to_api_dict(),
        )

    async def delete_equity_grant(
        self,
        employee_id: str,
        grant_id: int,
    ) -> None:
        """Delete an equity grant.

        Args:
            employee_id: The employee ID.
            grant_id: The equity grant ID.
        """
        await self._http.delete(f"/people/{employee_id}/equities/{grant_id}")

    # Variable Payment Methods
    async def get_variable_payments(self, employee_id: str) -> list[VariablePayment]:
        """Get variable payments for an employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of variable payments.
        """
        response = await self._http.get(f"/people/{employee_id}/variable")
        parsed = self._parse_response(response, VariablePaymentsResponse)
        return parsed.values

    async def create_variable_payment(
        self,
        employee_id: str,
        payment: VariablePaymentCreateRequest,
    ) -> VariablePayment:
        """Create a variable payment for an employee.

        Args:
            employee_id: The employee ID.
            payment: The variable payment data.

        Returns:
            The created variable payment.
        """
        response = await self._http.post(
            f"/people/{employee_id}/variable",
            json_data=payment.to_api_dict(),
        )
        return self._parse_response(response, VariablePayment)

    async def delete_variable_payment(
        self,
        employee_id: str,
        payment_id: int,
    ) -> None:
        """Delete a variable payment.

        Args:
            employee_id: The employee ID.
            payment_id: The variable payment ID.
        """
        await self._http.delete(f"/people/{employee_id}/variable/{payment_id}")

    # Training Record Methods
    async def get_training_records(self, employee_id: str) -> list[TrainingRecord]:
        """Get training records for an employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of training records.
        """
        response = await self._http.get(f"/people/{employee_id}/training")
        parsed = self._parse_response(response, TrainingHistoryResponse)
        return parsed.values

    async def create_training_record(
        self,
        employee_id: str,
        record: TrainingRecordCreateRequest,
    ) -> TrainingRecord:
        """Create a training record for an employee.

        Args:
            employee_id: The employee ID.
            record: The training record data.

        Returns:
            The created training record.
        """
        response = await self._http.post(
            f"/people/{employee_id}/training",
            json_data=record.to_api_dict(),
        )
        return self._parse_response(response, TrainingRecord)

    async def delete_training_record(
        self,
        employee_id: str,
        record_id: int,
    ) -> None:
        """Delete a training record.

        Args:
            employee_id: The employee ID.
            record_id: The training record ID.
        """
        await self._http.delete(f"/people/{employee_id}/training/{record_id}")

    # Bank Account Methods
    async def get_bank_accounts(self, employee_id: str) -> list[BankAccount]:
        """Get bank accounts for an employee.

        Args:
            employee_id: The employee ID.

        Returns:
            List of bank accounts.
        """
        response = await self._http.get(f"/people/{employee_id}/bank-accounts")
        parsed = self._parse_response(response, BankAccountsResponse)
        return parsed.values

    async def create_bank_account(
        self,
        employee_id: str,
        account: BankAccountCreateRequest,
    ) -> BankAccount:
        """Create a bank account for an employee.

        Args:
            employee_id: The employee ID.
            account: The bank account data.

        Returns:
            The created bank account.
        """
        response = await self._http.post(
            f"/people/{employee_id}/bank-accounts",
            json_data=account.to_api_dict(),
        )
        return self._parse_response(response, BankAccount)

    async def update_bank_account(
        self,
        employee_id: str,
        account_id: int,
        account: BankAccountUpdateRequest,
    ) -> None:
        """Update a bank account.

        Args:
            employee_id: The employee ID.
            account_id: The bank account ID.
            account: The updated bank account data.
        """
        await self._http.put(
            f"/people/{employee_id}/bank-accounts/{account_id}",
            json_data=account.to_api_dict(),
        )

    async def delete_bank_account(
        self,
        employee_id: str,
        account_id: int,
    ) -> None:
        """Delete a bank account.

        Args:
            employee_id: The employee ID.
            account_id: The bank account ID.
        """
        await self._http.delete(f"/people/{employee_id}/bank-accounts/{account_id}")
