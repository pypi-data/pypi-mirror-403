"""Generate ERD-style D2 diagrams from Pydantic models."""

from pydantic_diagram.core import (
    render_d2,
    build_graph,
    collect_models,
    Table,
    TableRow,
    Edge,
    Node,
    RowRef,
)

__all__ = [
    "render_d2",
    "build_graph",
    "collect_models",
    "Table",
    "TableRow",
    "Edge",
    "Node",
    "RowRef",
]
