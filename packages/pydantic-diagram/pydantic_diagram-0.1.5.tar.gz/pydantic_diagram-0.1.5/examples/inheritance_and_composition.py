"""Example demonstrating both inheritance and composition relationships."""

from __future__ import annotations

from pydantic import BaseModel, Field

from pydantic_diagram import render_d2


class Person(BaseModel):
    """Base class representing any person."""

    name: str
    email: str = Field(description="Contact email address")


class Employee(Person):
    """An employee in the company, inherits from Person."""

    employee_id: int
    hire_date: str = Field(description="Date of hire (YYYY-MM-DD)")


class Manager(Employee):
    """A manager, inherits from Employee."""

    department_name: str
    direct_reports: list[Employee] = Field(
        default_factory=list, description="Employees reporting to this manager"
    )


class Address(BaseModel):
    """A physical address."""

    street: str
    city: str
    country: str
    postal_code: str


class Department(BaseModel):
    """A department within the company."""

    name: str
    budget: float = Field(description="Annual budget in USD")
    manager: Manager = Field(description="Department head")
    employees: list[Employee] = Field(
        default_factory=list, description="All employees in department"
    )


class Company(BaseModel):
    """A company with departments and headquarters."""

    name: str
    headquarters: Address
    departments: list[Department] = Field(default_factory=list)


ALL_MODELS = [Person, Employee, Manager, Address, Department, Company]


if __name__ == "__main__":
    print("=" * 70)
    print("INHERITANCE AND COMPOSITION FLAG DEMO")
    print("=" * 70)
    print()

    # Default: Both inheritance and composition shown
    print("# 1. DEFAULT (show_inheritance=True, show_composition=True)")
    print("# Shows all relationships: inheritance arrows and composition edges")
    print("-" * 70)
    print(render_d2(ALL_MODELS))
    print()

    # Only inheritance (no composition edges)
    print(
        "# 2. INHERITANCE ONLY (show_inheritance=True, show_composition=False)"
    )
    print("# Shows class hierarchy but no field-based relationships")
    print("-" * 70)
    print(render_d2(ALL_MODELS, show_inheritance=True, show_composition=False))
    print()

    # Only composition (no inheritance arrows)
    print(
        "# 3. COMPOSITION ONLY (show_inheritance=False, show_composition=True)"
    )
    print("# Shows field relationships but no class hierarchy")
    print("-" * 70)
    print(render_d2(ALL_MODELS, show_inheritance=False, show_composition=True))
    print()

    # Neither (just the tables)
    print("# 4. TABLES ONLY (show_inheritance=False, show_composition=False)")
    print("# Shows only the model schemas without any relationship edges")
    print("-" * 70)
    print(render_d2(ALL_MODELS, show_inheritance=False, show_composition=False))
