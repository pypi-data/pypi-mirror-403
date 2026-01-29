"""Example with self-referential models (tree structures)."""

from __future__ import annotations

from pydantic import BaseModel

from pydantic_diagram import render_d2


class TreeNode(BaseModel):
    """A node in a tree structure."""
    
    value: str
    children: list[TreeNode] = []


class Employee(BaseModel):
    """An employee who may have a manager."""
    
    name: str
    title: str
    manager: Employee | None = None
    reports: list[Employee] = []


if __name__ == "__main__":
    print("# TreeNode diagram:")
    print(render_d2([TreeNode]))
    print()
    print("# Employee diagram:")
    print(render_d2([Employee]))
