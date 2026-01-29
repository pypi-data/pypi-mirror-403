# 🐍 PyBob SDK

<div align="center">

**An unofficial Python SDK for the HiBob HR API**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-green.svg)](https://pydantic.dev/)
[![Async](https://img.shields.io/badge/Async-httpx-orange.svg)](https://www.python-httpx.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENCE)

[Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Documentation](https://apidocs.hibob.com/reference/getting-started-with-bob-api)

</div>

---

## 📦 Installation

```bash
# Using uv
uv add pybob-sdk

# Using pip
pip install pybob-sdk
```

## 🚀 Quick Start

### 1. Set up credentials

```bash
export BOB_SERVICE_ACCOUNT_ID="your_service_account_id"
export BOB_SERVICE_ACCOUNT_TOKEN="your_service_account_token"
```

Or create a `.env` file:

```env
BOB_SERVICE_ACCOUNT_ID=your_id
BOB_SERVICE_ACCOUNT_TOKEN=your_token
```

### 2. Use the SDK

```python
import asyncio
from pybob_sdk import Bob

async def main():
    async with Bob() as bob:
        # Search for employees
        results = await bob.people.search(
            fields=["root.id", "root.fullName", "root.email"],
            filters=[{
                "fieldPath": "root.email",
                "operator": "equals",
                "values": ["anakin.skywalker@company.com"]
            }]
        )
        
        for employee in results.employees:
            print(f"{employee.full_name} - {employee.email}")

asyncio.run(main())
```

## 🔐 Authentication

The SDK supports multiple authentication methods:

Credentials are automatically loaded from environment variables or `.env` files:

```python
from pybob_sdk import Bob

async with Bob() as bob:
    ...
```

Alternatively explicit credentials:

```python
bob = Bob(
    service_account_id="YOUR_ID",
    service_account_token="YOUR_TOKEN",
)
```

## 📚 API Reference

### 👥 People API

```python
# Search employees
results = await bob.people.search(
    fields=["root.id", "root.fullName", "root.email"],
    filters=[{
        "fieldPath": "root.department",
        "operator": "equals",
        "values": ["Engineering"]
    }]
)

# Get public profiles
profiles = await bob.people.get_public_profiles()

# Get employee by ID
employee = await bob.people.get("123456789")
```

### 📊 Employee Tables API

```python
# Get employment history
history = await bob.employee_tables.get_employment_history("123456789")

for entry in history:
    if entry.working_pattern and entry.working_pattern.days:
        days = entry.working_pattern.days
        print(f"Monday: {days.monday} hours")

# Get work history
work_history = await bob.employee_tables.get_work_history("123456789")
```

### 🏖️ Time Off API

```python
# Get who's out today
out_today = await bob.time_off.get_whos_out_today()
for person in out_today:
    print(f"{person.name} - {person.policy_type}")

# Get policy types
policy_types = await bob.time_off.get_policy_types()
```

### ✅ Tasks API

```python
# Get all open tasks
tasks = await bob.tasks.get_open_tasks()

# Get employee tasks
employee_tasks = await bob.tasks.get_employee_tasks("123456789")

# Complete a task
await bob.tasks.complete_task("task_123")
```

### 📈 Reports API

```python
# Get all reports
reports = await bob.reports.get_reports()

# Download a report
data = await bob.reports.download_report_by_id("report_123")
```

### 🎯 Onboarding API

```python
# Get onboarding wizards
wizards = await bob.onboarding.get_wizards()
for wizard in wizards:
    print(f"{wizard.name} (ID: {wizard.id})")
```

### 📋 Metadata API

```python
# Get employee fields
fields = await bob.metadata.get_fields()

# Get company lists
lists = await bob.metadata.get_lists()

# Get specific list
departments = await bob.metadata.get_list("department")
```

### 💼 Job Catalog API

```python
# Get job roles
roles = await bob.job_catalog.get_roles()

# Get job families
families = await bob.job_catalog.get_families()

# Search job profiles
profiles = await bob.job_catalog.search_profiles()
```

## 🛠️ Development

### Setup

```bash
git clone https://github.com/kurtismassey/pybob.git
cd pybob
uv sync --all-extras
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy pybob_sdk
```