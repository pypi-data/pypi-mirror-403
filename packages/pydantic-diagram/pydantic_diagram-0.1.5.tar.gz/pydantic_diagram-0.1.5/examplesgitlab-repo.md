# Codebase Compilation: examplesgitlab-repo.md

Folders Scanned: `.`

## File and Folder Structure

```
├── pydantic-diagram/
│   │   ├── README.md
│   │   └── pyproject.toml
│   └── examples/
│   │       ├── basic.py
│   │       ├── inheritance.py
│   │       ├── inheritance_and_composition.py
│   │       └── self_referential.py
│   ├── src/
│   │   └── pydantic_diagram/
│   │   │       ├── __init__.py
│   │   │       ├── cli.py
│   │   │       └── core.py
```

---

## `examples\basic.py`

```py
"""Basic example: simple user/post models."""

from pydantic import BaseModel, Field

from pydantic_diagram import render_d2


class User(BaseModel):
    """A user in the system."""
    
    id: int
    name: str
    email: str = Field(description="Primary email address")


class Post(BaseModel):
    """A blog post written by a user."""
    
    id: int
    title: str
    body: str
    author: User


if __name__ == "__main__":
    print(render_d2([User, Post]))
```

## `examples\inheritance.py`

```py
"""Example showing model inheritance."""

from pydantic import BaseModel

from pydantic_diagram import render_d2


class Animal(BaseModel):
    """Base class for animals."""
    
    name: str
    age: int


class Dog(Animal):
    """A dog."""
    
    breed: str
    is_good_boy: bool = True


class Cat(Animal):
    """A cat."""
    
    indoor: bool
    lives_remaining: int = 9


if __name__ == "__main__":
    print(render_d2([Animal, Dog, Cat]))
```

## `examples\inheritance_and_composition.py`

```py
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
```

## `examples\self_referential.py`

```py
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
```

## `pyproject.toml`

```toml
[project]
name = "pydantic-diagram"
version = "0.1.4"
description = "Generate ERD-style D2 diagrams from Pydantic models"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [
    { name = "Your Name", email = "you@example.com" }
]
keywords = ["pydantic", "diagram", "d2", "erd", "visualization"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Documentation",
    "Typing :: Typed",
]
dependencies = [
    "pydantic>=2.0",
    "typenames>=2.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "ruff>=0.1.0",
]

[project.scripts]
pydantic-diagram = "pydantic_diagram.cli:main"

[project.urls]
Homepage = "https://github.com/yourusername/pydantic-diagram"
Repository = "https://github.com/yourusername/pydantic-diagram"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/pydantic_diagram"]

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
```

## `README.md`

```md
# pydantic-diagram

Generate ERD-style diagrams from your Pydantic models using [D2](https://d2lang.com/).

Takes a set of Pydantic models and outputs D2 code that renders as a nice visual diagram showing model relationships, inheritance, and field types.

## Installation

```bash
pip install pydantic-diagram
```

## Usage

### As a library

```python
from pydantic import BaseModel
from pydantic_diagram import render_d2

class User(BaseModel):
    id: int
    name: str

class Post(BaseModel):
    id: int
    title: str
    author: User

# Generate D2 code
# Options allow you to toggle specific features
d2_code = render_d2(
    [User, Post],
    show_inheritance=True,
    show_composition=True
)
print(d2_code)
```

### From the command line

```bash
# From a file path (no install needed)
pydantic-diagram path/to/models.py:User,Post

# From an installed module
pydantic-diagram myapp.models:User,Post

# Diagram all models in a module/file
pydantic-diagram myapp.models

# Write to file, then render with D2
pydantic-diagram models.py -o schema.d2
d2 schema.d2 schema.svg
```

### CLI options

```
pydantic-diagram <module:models> [options]

Options:
  -o, --output FILE          Write to file instead of stdout
  --direction DIR            Layout direction: right, down, left, up (default: right)
  --no-inherited             Exclude inherited fields from subclasses
  --no-inheritance-edges     Do not draw inheritance (extends) arrows
  --no-composition-edges     Do not draw composition/relation arrows
  --qualified-names          Use fully qualified names (module.ClassName)
  --no-docstrings            Exclude docstrings and field descriptions
```

## What it diagrams

- **Model relationships**: composition, collections, unions
- **Inheritance**: shows parent/child class relationships
- **Field types**: rendered as D2 sql_table shapes
- **Self-references**: handles recursive models correctly
- **Docstrings**: model and field descriptions appear as tooltips/constraints

## Requirements

- Python 3.10+
- Pydantic 2.0+
- [D2](https://d2lang.com/) (for rendering the output)

## License

MIT
```

## `src\pydantic_diagram\__init__.py`

```py
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
```

## `src\pydantic_diagram\cli.py`

```py
"""Minimal CLI for pydantic-diagram."""

import argparse
import sys
from importlib import import_module, util
from pathlib import Path

from pydantic import BaseModel

from pydantic_diagram import render_d2


def _import_module(module_path: str):
    # Check if it looks like a path
    p = Path(module_path)
    if (
        "/" in module_path or "\\" in module_path or module_path.endswith(".py")
    ) and p.exists():
        mod_name = p.stem
        spec = util.spec_from_file_location(mod_name, str(p))
        if spec is None or spec.loader is None:
            print(
                f"Error: Could not load module from file '{module_path}'",
                file=sys.stderr,
            )
            sys.exit(1)
        module = util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
        return module

    # If not a file, try to import as an installed module/package
    try:
        return import_module(module_path)
    except ImportError as e:
        print(
            f"Error: Could not import module '{module_path}': {e}",
            file=sys.stderr,
        )
        sys.exit(1)


def _import_models(spec: str) -> list[type[BaseModel]]:
    """
    Import models from a module:attribute spec.

    Examples:
        myapp.models:User
        myapp.models:User,Post,Comment
        myapp.models  (imports all BaseModel subclasses from module)
    """
    if ":" in spec:
        module_path, attrs = spec.rsplit(":", 1)
        attr_names = [a.strip() for a in attrs.split(",")]
    else:
        module_path = spec
        attr_names = None

    try:
        module = _import_module(module_path)
    except ImportError as e:
        print(
            f"Error: Could not import module '{module_path}': {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    models: list[type[BaseModel]] = []

    if attr_names:
        for name in attr_names:
            obj = getattr(module, name, None)
            if obj is None:
                print(
                    f"Error: '{name}' not found in {module_path}",
                    file=sys.stderr,
                )
                sys.exit(1)
            if not (isinstance(obj, type) and issubclass(obj, BaseModel)):
                print(
                    f"Error: '{name}' is not a Pydantic BaseModel",
                    file=sys.stderr,
                )
                sys.exit(1)
            models.append(obj)
    else:
        # Find all BaseModel subclasses in module
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseModel)
                and obj is not BaseModel
                and obj.__module__ == module.__name__
            ):
                models.append(obj)

        if not models:
            print(
                f"Error: No Pydantic models found in {module_path}",
                file=sys.stderr,
            )
            sys.exit(1)

    return models


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pydantic-diagram",
        description="Generate D2 diagrams from Pydantic models",
    )
    parser.add_argument(
        "models",
        help="Module and models to diagram (e.g. myapp.models:User,Post or myapp.models)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--direction",
        choices=["right", "down", "left", "up"],
        default="right",
        help="Layout direction (default: right)",
    )
    parser.add_argument(
        "--no-inherited",
        action="store_true",
        help="Exclude inherited fields from subclasses",
    )
    parser.add_argument(
        "--qualified-names",
        action="store_true",
        help="Use fully qualified class names (module.Class)",
    )
    parser.add_argument(
        "--no-docstrings",
        action="store_true",
        help="Exclude docstrings and field descriptions",
    )
    parser.add_argument(
        "--no-inheritance-edges",
        action="store_true",
        help="Do not draw inheritance (extends) arrows",
    )
    parser.add_argument(
        "--no-composition-edges",
        action="store_true",
        help="Do not draw composition/relation arrows",
    )

    args = parser.parse_args()

    models = _import_models(args.models)

    d2_code = render_d2(
        models,
        direction=args.direction,
        include_inherited_rows=not args.no_inherited,
        qualified_names=args.qualified_names,
        include_docstrings=not args.no_docstrings,
        show_inheritance=not args.no_inheritance_edges,
        show_composition=not args.no_composition_edges,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(d2_code)
        print(f"Wrote D2 diagram to {args.output}", file=sys.stderr)
    else:
        print(d2_code)


if __name__ == "__main__":
    main()
```

## `src\pydantic_diagram\core.py`

```py
from __future__ import annotations

import enum
import inspect
import re
import sys
import types
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel

try:
    from typenames import DEFAULT_REMOVE_MODULES
    from typenames import typenames as _typenames

    HAS_TYPENAMES = True
except ImportError:
    HAS_TYPENAMES = False
    DEFAULT_REMOVE_MODULES = []

# Handle Self type (3.11+ in typing, earlier in typing_extensions)
if sys.version_info >= (3, 11):
    from typing import Self as _Self
else:
    try:
        from typing_extensions import Self as _Self
    except ImportError:
        _Self = None  # type: ignore[misc,assignment]


# ============================================================
# D2 helpers
# ============================================================

_D2_RESERVED: set[str] = {
    "shape",
    "label",
    "style",
    "width",
    "height",
    "near",
    "direction",
    "top",
    "bottom",
    "left",
    "right",
    "icon",
    "tooltip",
    "link",
    "source-arrowhead",
    "target-arrowhead",
}

_SIMPLE_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _d2_quote(s: str) -> str:
    esc = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{esc}"'


def d2_id(token: str) -> str:
    if token in _D2_RESERVED or not _SIMPLE_ID_RE.match(token):
        return _d2_quote(token)
    return token


def d2_string_value(v: str) -> str:
    if v == "" or any(ch in v for ch in ['"', "{", "}", "\n"]):
        return _d2_quote(v)
    return v


class D2Writer:
    def __init__(self, indent: str = "  "):
        self._lines: list[str] = []
        self._indent = indent
        self._level = 0

    def line(self, s: str = "") -> None:
        self._lines.append(f"{self._indent * self._level}{s}".rstrip())

    def block_start(self, head: str) -> None:
        self.line(f"{head}: {{")
        self._level += 1

    def block_end(self) -> None:
        self._level = max(0, self._level - 1)
        self.line("}")

    def render(self) -> str:
        while self._lines and self._lines[-1] == "":
            self._lines.pop()
        return "\n".join(self._lines) + "\n"


def _render_style_kv(w: D2Writer, d: Mapping[str, Any]) -> None:
    for k, v in d.items():
        if isinstance(v, bool):
            vv = "true" if v else "false"
        elif isinstance(v, (int, float)):
            vv = str(v)
        else:
            vv = d2_string_value(str(v))
        w.line(f"{k}: {vv}")


# ============================================================
# Type inspection helpers
# ============================================================

_WORD = r"[A-Za-z_][A-Za-z0-9_]*"

# Best-effort stdlib detection (3.10+). Falls back gracefully on older Pythons.
_STDLIB_ROOTS: frozenset[str] = getattr(sys, "stdlib_module_names", frozenset())


def _module_root(mod: str) -> str:
    return mod.split(".", 1)[0]


def _matches_prefix(mod: str, prefix: str) -> bool:
    """
    Dot-safe prefix match:
      - "foo" matches "foo" and "foo.bar"
      - "foo." matches "foo.bar" (and deeper), but not "foobar"
    """
    if not prefix:
        return False
    if prefix.endswith("."):
        return mod.startswith(prefix)
    return mod == prefix or mod.startswith(prefix + ".")


def _should_exclude_from_name_shortening(
    mod: str,
    *,
    exclude_stdlib: bool = True,
    exclude_module_prefixes: Sequence[str] = (),
) -> bool:
    """
    Determine if types from this module should be excluded from 
    minimal-unique-name calculation.
    
    Excludes: builtins, typing machinery, stdlib (optional), 
    and caller-specified prefixes.
    """
    if not mod:
        return True

    # builtins are always "plumbing"
    if mod == "builtins":
        return True

    # typing machinery (typing_extensions isn't stdlib, but still plumbing)
    if _matches_prefix(mod, "typing") or _matches_prefix(
        mod, "typing_extensions"
    ):
        return True

    # optional: exclude all stdlib modules by root name
    if exclude_stdlib and _module_root(mod) in _STDLIB_ROOTS:
        return True

    # caller/project-specific exclusions
    for p in exclude_module_prefixes:
        if _matches_prefix(mod, p):
            return True

    return False


def _iter_class_keyparts(
    c: Any,
    *,
    exclude_stdlib: bool = True,
    exclude_module_prefixes: Sequence[str] = (),
) -> tuple[str, list[str], str] | None:
    """
    Return (full, module_parts, qual) for "interesting" classes, else None.
    """
    if not inspect.isclass(c):
        return None

    mod = getattr(c, "__module__", "") or ""
    qual = getattr(c, "__qualname__", "") or getattr(c, "__name__", "") or ""
    if not (mod and qual):
        return None

    if _should_exclude_from_name_shortening(
        mod,
        exclude_stdlib=exclude_stdlib,
        exclude_module_prefixes=exclude_module_prefixes,
    ):
        return None

    full = f"{mod}.{qual}"
    return full, mod.split("."), qual


def iter_named_classes(
    tp: Any,
    *,
    localns: Mapping[str, Any] | None = None,
    _seen: set[int] | None = None,
    exclude_stdlib: bool = True,
    exclude_module_prefixes: Sequence[str] = (),
) -> set[type]:
    """
    Collect all non-plumbing classes referenced inside a type annotation.
    (Enums and other non-BaseModel classes included.)
    """
    if _seen is None:
        _seen = set()

    tp_id = id(tp)
    if tp_id in _seen:
        return set()
    _seen.add(tp_id)

    out: set[type] = set()

    def rec(x: Any) -> None:
        try:
            x = unwrap_annotated(x)
            x, _ = unwrap_optional(x)
        except Exception:
            return

        if _is_self_type(x):
            return

        fr = _forwardref_arg(x)
        if fr is not None:
            if localns and fr in localns:
                rec(localns[fr])
            return

        if _iter_class_keyparts(
            x,
            exclude_stdlib=exclude_stdlib,
            exclude_module_prefixes=exclude_module_prefixes,
        ):
            out.add(x)

        origin = get_origin(x)
        args = get_args(x)

        if _is_union_origin(origin):
            for a in args:
                if a is type(None):
                    continue
                rec(a)
            return

        if _is_sequence_origin(origin) or _is_mapping_origin(origin):
            for a in args:
                if a is Ellipsis or a is type(None):
                    continue
                rec(a)
            return

    rec(tp)
    return out


def _minimal_unique_type_name_map(
    classes: set[type],
    *,
    exclude_stdlib: bool = True,
    exclude_module_prefixes: Sequence[str] = (),
) -> dict[str, str]:
    """
    Map 'module.QualName' -> shortest unique display name.
    Preference order per class:
      QualName
      <last_module>.QualName
      <last2_module>.<last_module>.QualName
      ...
      full module.QualName
    """
    infos: dict[str, tuple[list[str], str]] = {}
    maxk = 0

    for c in classes:
        kp = _iter_class_keyparts(
            c,
            exclude_stdlib=exclude_stdlib,
            exclude_module_prefixes=exclude_module_prefixes,
        )
        if not kp:
            continue
        full, module_parts, qual = kp
        infos[full] = (module_parts, qual)
        maxk = max(maxk, len(module_parts))

    unresolved = set(infos.keys())
    mapping: dict[str, str] = {}

    k = 0
    while unresolved and k <= maxk:
        groups: dict[str, list[str]] = {}
        for full in unresolved:
            module_parts, qual = infos[full]
            cand = qual if k == 0 else ".".join(module_parts[-k:] + [qual])
            groups.setdefault(cand, []).append(full)

        newly_resolved: set[str] = set()
        for cand, fulls in groups.items():
            if len(fulls) == 1:
                only = fulls[0]
                mapping[only] = cand
                newly_resolved.add(only)

        unresolved -= newly_resolved
        k += 1

    # anything still ambiguous keeps full qualification
    for full in unresolved:
        mapping[full] = full

    return mapping


def _shorten_type_string(s: str, name_map: Mapping[str, str]) -> str:
    """
    Replace occurrences of fully-qualified class names inside a rendered type string.
    """
    items = sorted(name_map.items(), key=lambda kv: len(kv[0]), reverse=True)
    for full, disp in items:
        s = re.sub(
            rf"(?<![A-Za-z0-9_]){re.escape(full)}(?![A-Za-z0-9_])",
            disp,
            s,
        )
    return s


def is_model_class(tp: Any) -> bool:
    try:
        return inspect.isclass(tp) and issubclass(tp, BaseModel)
    except (TypeError, AttributeError):
        return False


def _is_self_type(tp: Any) -> bool:
    """Check if tp is typing.Self or typing_extensions.Self."""
    if _Self is not None and tp is _Self:
        return True
    # String fallback for edge cases
    return str(tp) in ("typing.Self", "typing_extensions.Self", "Self")


def unwrap_annotated(tp: Any) -> Any:
    """Robustly unwrap Annotated types."""
    if hasattr(tp, "__metadata__") and hasattr(tp, "__origin__"):
        return tp.__origin__
    origin = get_origin(tp)
    if origin is not None and "Annotated" in str(origin):
        args = get_args(tp)
        return args[0] if args else tp
    return tp


def _is_union_origin(origin: Any) -> bool:
    return origin is Union or (
        hasattr(types, "UnionType") and origin is types.UnionType
    )


def _forwardref_arg(tp: Any) -> str | None:
    """Extract string from ForwardRef, or None."""
    # typing.ForwardRef
    if hasattr(tp, "__forward_arg__"):
        arg = tp.__forward_arg__
        return arg if isinstance(arg, str) else None
    # Sometimes it's just a string annotation
    if isinstance(tp, str):
        return tp
    return None


def unwrap_optional(tp: Any) -> tuple[Any, bool]:
    tp = unwrap_annotated(tp)
    origin = get_origin(tp)
    if _is_union_origin(origin):
        args = get_args(tp)
        if any(a is type(None) for a in args):
            non_none = tuple(a for a in args if a is not type(None))
            if len(non_none) == 1:
                return non_none[0], True
            return Union[non_none], True  # type: ignore[misc]
    return tp, False


def _is_sequence_origin(origin: Any) -> bool:
    return origin in (list, set, frozenset, tuple, Sequence)


def _is_mapping_origin(origin: Any) -> bool:
    return origin in (dict, Mapping)


# ============================================================
# Pydantic version compatibility
# ============================================================


def _get_model_fields(m: type[BaseModel]) -> dict[str, Any]:
    """
    Get model fields dict, compatible with Pydantic v1 and v2.

    Returns dict mapping field name -> field info object.
    """
    # Pydantic v2
    if hasattr(m, "model_fields"):
        return m.model_fields
    fields = getattr(m, "__fields__", None)
    if fields is not None:
        return fields
    raise TypeError(
        f"{m.__name__!r} has no model_fields or __fields__. "
        f"Is this a valid Pydantic model? (Supports Pydantic v1.x and v2.x)"
    )


def _get_field_annotation(field_info: Any) -> Any:
    """
    Get the type annotation from a field info object.

    Handles differences between Pydantic v1 and v2 field info.
    """
    # Pydantic v2: annotation attribute
    if hasattr(field_info, "annotation"):
        return field_info.annotation
    # Pydantic v1: outer_type_ attribute
    if hasattr(field_info, "outer_type_"):
        return field_info.outer_type_
    # Fallback
    return Any


# ============================================================
# Docstring extraction helpers
# ============================================================


def _normalise_whitespace(s: str) -> str:
    """Collapse all whitespace (including newlines) into single spaces."""
    return " ".join(s.split())


def _get_model_docstring(m: type[BaseModel]) -> str | None:
    """Extract cleaned docstring from a model class."""
    doc = getattr(m, "__doc__", None)
    if not doc:
        return None
    cleaned = _normalise_whitespace(doc)
    return cleaned if cleaned else None


def _get_field_description(field_info: Any) -> str | None:
    """Extract field description from Pydantic field info."""
    desc: str | None = None
    # Pydantic v2
    if hasattr(field_info, "description") and field_info.description:
        desc = field_info.description
    # Pydantic v1
    elif hasattr(field_info, "field_info"):
        inner = field_info.field_info
        if hasattr(inner, "description") and inner.description:
            desc = inner.description

    if desc:
        return _normalise_whitespace(desc)
    return None


# ============================================================
# Namespace resolution for forward references
# ============================================================


def _build_resolution_namespace(
    m: type[BaseModel],
    extra_ns: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a namespace for resolving forward references in model annotations.

    Includes:
    - Module globals (where the model is defined)
    - Class namespace (vars of the model)
    - Any extra namespace passed in

    This ensures self-referential types like `list["Node"]` resolve correctly.
    """
    ns: dict[str, Any] = {}

    # 1. Module globals - most important for forward refs
    module_name = getattr(m, "__module__", None)
    if module_name:
        import sys

        module = sys.modules.get(module_name)
        if module is not None:
            # Get module's global namespace
            ns.update(
                {
                    k: v
                    for k, v in vars(module).items()
                    if not k.startswith("_")  # Skip private/dunder
                }
            )

    # 2. Class namespace (for nested classes, class-level definitions)
    try:
        ns.update(vars(m))
    except TypeError:
        pass  # Some weird edge cases with vars()

    # 3. The class itself (critical for self-references)
    ns[m.__name__] = m

    # 4. Extra namespace passed by caller
    if extra_ns:
        ns.update(extra_ns)

    return ns


# ============================================================
# Type string rendering
# ============================================================


def _fallback_type_str(tp: Any) -> str:
    """Manual fallback when typenames unavailable or fails."""
    tp = unwrap_annotated(tp)

    if isinstance(tp, str):
        return tp

    fr = _forwardref_arg(tp)
    if fr is not None:
        return fr

    if _is_self_type(tp):
        return "Self"

    origin = get_origin(tp)
    args = get_args(tp)

    if _is_union_origin(origin):
        inner, opt = unwrap_optional(tp)
        if opt:
            return f"Optional[{_fallback_type_str(inner)}]"
        return " | ".join(_fallback_type_str(a) for a in args)

    if _is_sequence_origin(origin):
        if origin is tuple:
            if not args:
                return "tuple"
            if len(args) == 2 and args[1] is Ellipsis:
                return f"tuple[{_fallback_type_str(args[0])}, ...]"
            return (
                "tuple[" + ", ".join(_fallback_type_str(a) for a in args) + "]"
            )
        inner = _fallback_type_str(args[0]) if args else "Any"
        name = {
            list: "list",
            set: "set",
            frozenset: "frozenset",
            Sequence: "Sequence",
        }.get(origin, "list")
        return f"{name}[{inner}]"

    if _is_mapping_origin(origin):
        k = _fallback_type_str(args[0]) if len(args) >= 1 else "Any"
        v = _fallback_type_str(args[1]) if len(args) >= 2 else "Any"
        name = {dict: "dict", Mapping: "Mapping"}.get(origin, "dict")
        return f"{name}[{k}, {v}]"

    if "Literal" in str(origin):
        return "Literal[" + ", ".join(repr(a) for a in args) + "]"

    try:
        if inspect.isclass(tp):
            if issubclass(tp, enum.Enum):
                return tp.__name__
            return tp.__name__
    except (TypeError, AttributeError):
        pass

    # Last resort
    s = str(tp)
    for prefix in ("typing.", "typing_extensions.", "collections.abc."):
        s = s.replace(prefix, "")
    return s


def type_to_py_str(
    tp: Any, *, name_map: Mapping[str, str] | None = None
) -> str:
    """
    Render a readable Python type string.
    Uses typenames library if available, with fallback.
    """
    if not HAS_TYPENAMES:
        s = _fallback_type_str(tp)
        return _shorten_type_string(s, name_map) if name_map else s

    try:
        s = _typenames(
            tp,
            remove_modules=DEFAULT_REMOVE_MODULES
            + ["pydantic", "pydantic.fields"],
            include_extras=False,
            optional_syntax="optional_special_form",
        )
    except Exception:
        s = _fallback_type_str(tp)

    return _shorten_type_string(s, name_map) if name_map else s


# ============================================================
# Relationship detection (hardened)
# ============================================================


def iter_model_types(
    tp: Any,
    *,
    localns: Mapping[str, Any] | None = None,
    _seen: set[int] | None = None,
) -> set[type[BaseModel]]:
    """
    Return all BaseModel subclasses nested inside `tp`.
    Handles Self, forward refs, unions, containers, etc.

    Args:
        localns: Optional namespace for resolving forward refs
        _seen: Internal cycle detection (by id)
    """
    if _seen is None:
        _seen = set()

    # Cycle detection on type object identity
    tp_id = id(tp)
    if tp_id in _seen:
        return set()
    _seen.add(tp_id)

    out: set[type[BaseModel]] = set()

    def rec(x: Any) -> None:
        try:
            x = unwrap_annotated(x)
            x, _ = unwrap_optional(x)
        except Exception:
            return

        # Skip Self (would cause infinite recursion in self-referential models)
        if _is_self_type(x):
            return

        # Handle forward references
        fr = _forwardref_arg(x)
        if fr is not None:
            # Try to resolve from localns
            if localns and fr in localns:
                resolved = localns[fr]
                if is_model_class(resolved):
                    out.add(resolved)
            # Can't resolve - skip (will show as string in type_to_py_str)
            return

        if is_model_class(x):
            out.add(x)
            return

        origin = get_origin(x)
        args = get_args(x)

        if _is_union_origin(origin):
            for a in args:
                if a is type(None):
                    continue
                rec(a)
            return

        if _is_sequence_origin(origin):
            for a in args:
                if a is Ellipsis:
                    continue
                rec(a)
            return

        if _is_mapping_origin(origin):
            for a in args:
                rec(a)
            return

    try:
        rec(tp)
    except Exception:
        # Defensive: don't crash on weird types
        pass

    return out


def relationship_kind(tp: Any) -> str | None:
    """Classify edge semantics for a field type."""
    try:
        t0 = unwrap_annotated(tp)
        t0, _ = unwrap_optional(t0)
    except Exception:
        return None

    # Self type is composition (to the same model)
    if _is_self_type(t0):
        return "composition"

    if is_model_class(t0):
        return "composition"

    origin = get_origin(t0)

    if _is_union_origin(origin):
        targets = iter_model_types(t0)
        return "union" if targets else None

    if _is_sequence_origin(origin) or _is_mapping_origin(origin):
        targets = iter_model_types(t0)
        return "collection" if targets else None

    return None


# ============================================================
# D2 metadata hooks
# ============================================================


def get_d2_meta(field_info: Any) -> dict[str, Any]:
    extra = getattr(field_info, "json_schema_extra", None)
    if isinstance(extra, dict):
        d2 = extra.get("d2")
        if isinstance(d2, dict):
            return dict(d2)
    return {}


# ============================================================
# Graph model
# ============================================================


@dataclass(frozen=True)
class Node:
    model: type[BaseModel]
    name: str


@dataclass(frozen=True)
class RowRef:
    node: Node
    row: str | None = None


@dataclass(frozen=True)
class Edge:
    src: RowRef
    dst: RowRef
    kind: str
    label: str | None = None
    source_arrow: dict[str, Any] | None = None
    target_arrow: dict[str, Any] | None = None
    style: dict[str, Any] | None = None


@dataclass
class TableRow:
    name: str
    type_str: str
    constraint: str | None = None


@dataclass
class Table:
    node: Node
    rows: list[TableRow] = field(default_factory=list)


# ============================================================
# Model discovery (with qualified names option)
# ============================================================


def _model_display_name(m: type[BaseModel], *, qualified: bool = False) -> str:
    """Get display name, optionally module-qualified to avoid collisions."""
    if qualified:
        module = getattr(m, "__module__", "")
        if module and module != "__main__":
            return f"{module}.{m.__name__}"
    return m.__name__


def collect_models(
    roots: Iterable[type[BaseModel]],
    *,
    localns: dict[str, Any] | None = None,
) -> set[type[BaseModel]]:
    """Collect models reachable via field annotations and inheritance."""
    seen: set[type[BaseModel]] = set()
    stack = list(roots)

    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)

        # Inheritance chain
        for b in getattr(m, "__bases__", ()):
            if is_model_class(b) and b is not BaseModel:
                stack.append(b)

        # Field references
        model_ns = _build_resolution_namespace(m, localns)
        for finfo in _get_model_fields(m).values():
            ann = _get_field_annotation(finfo)
            for t in iter_model_types(ann, localns=model_ns):
                stack.append(t)

    return seen


# ============================================================
# Build tables + edges (with Self handling)
# ============================================================


def build_graph(
    roots: Iterable[type[BaseModel]],
    *,
    include_inherited_rows: bool = True,
    qualified_names: bool = False,
    include_docstrings: bool = True,
    shorten_type_names: bool = True,
    show_inheritance: bool = True, 
    show_composition: bool = True,
) -> tuple[list[Table], list[Edge]]:
    """
    Build graph of tables and edges.

    Args:
        roots: Root model classes to start from
        include_inherited_rows: Include fields from parent classes
        qualified_names: Use module.ClassName to avoid collisions
    """
    model_set = collect_models(roots)
    models = sorted(model_set, key=lambda c: c.__name__)

    name_map: dict[str, str] | None = None
    if shorten_type_names:
        classes: set[type] = set()
        for m in models:
            classes.add(m)
            model_ns = _build_resolution_namespace(m)
            for finfo in _get_model_fields(m).values():
                ann = _get_field_annotation(finfo)
                classes |= iter_named_classes(ann, localns=model_ns)
        name_map = _minimal_unique_type_name_map(classes)

    nodes = {
        m: Node(m, _model_display_name(m, qualified=qualified_names))
        for m in models
    }

    tables: list[Table] = []
    edges: list[Edge] = []

    # Inheritance edges
    if show_inheritance:
        for m in models:
            child = nodes[m]
            for b in getattr(m, "__bases__", ()):
                if is_model_class(b) and b is not BaseModel and b in nodes:
                    parent = nodes[b]
                    edges.append(
                        Edge(
                            src=RowRef(child, None),
                            dst=RowRef(parent, None),
                            kind="inheritance",
                            label="extends",
                            target_arrow={
                                "shape": "triangle",
                                "style.filled": False,
                            },
                            style={"stroke-dash": 3},
                        )
                    )

    # Tables + field edges
    for m in models:
        node = nodes[m]
        t = Table(node=node)
        declared = set(getattr(m, "__annotations__", {}).keys())
        model_ns = _build_resolution_namespace(m)

        for fname, finfo in _get_model_fields(m).items():
            if not include_inherited_rows and fname not in declared:
                continue

            ann = _get_field_annotation(finfo)
            type_str = type_to_py_str(ann, name_map=name_map)

            meta = get_d2_meta(finfo)
            rel_override = meta.get("relationship")
            edge_label = meta.get("edge_label")
            row_constraint = meta.get("constraint")

            # Determine constraint: explicit d2 meta takes priority,
            # then fall back to field description if docstrings enabled
            if isinstance(row_constraint, str) and row_constraint.strip():
                constraint = row_constraint.strip()
            elif include_docstrings:
                desc = _get_field_description(finfo)
                constraint = desc.strip() if desc else None
            else:
                constraint = None

            t.rows.append(
                TableRow(name=fname, type_str=type_str, constraint=constraint)
            )

            if rel_override == "skip":
                continue
            
            if not show_composition:
                continue

            src = RowRef(node, fname)
            kind = relationship_kind(ann)

            # Handle Self type specially
            ann_unwrapped = unwrap_annotated(ann)
            ann_unwrapped, _ = unwrap_optional(ann_unwrapped)

            if _is_self_type(ann_unwrapped):
                # Self-reference: edge to same model
                edges.append(
                    Edge(
                        src=src,
                        dst=RowRef(node, None),
                        kind="composition",
                        label=edge_label or "self",
                    )
                )
                continue

            targets = sorted(
                iter_model_types(ann, localns=model_ns),
                key=lambda c: c.__name__,
            )

            if not kind or not targets:
                continue

            # Apply relationship overrides
            if rel_override == "embed":
                edge_label = edge_label or "embedded"
            elif rel_override == "fk":
                edge_label = edge_label or "key_ref"
            elif rel_override == "ref":
                edge_label = edge_label or "ref"

            if kind == "composition":
                dst_model = targets[0]
                edges.append(
                    Edge(
                        src=src,
                        dst=RowRef(nodes[dst_model], None),
                        kind="composition",
                        label=edge_label,
                    )
                )
            elif kind == "union":
                for dst_model in targets:
                    edges.append(
                        Edge(
                            src=src,
                            dst=RowRef(nodes[dst_model], None),
                            kind="union",
                            label=edge_label or "one_of",
                        )
                    )
            elif kind == "collection":
                for dst_model in targets:
                    edges.append(
                        Edge(
                            src=src,
                            dst=RowRef(nodes[dst_model], None),
                            kind="collection",
                            label=edge_label or "many",
                            target_arrow={"shape": "cf-many"},
                        )
                    )

        tables.append(t)

    # Deduplicate edges
    uniq: dict[tuple, Edge] = {}
    for e in edges:
        k = (
            e.src.node.name,
            e.src.row,
            e.dst.node.name,
            e.dst.row,
            e.kind,
            e.label,
            str(e.source_arrow),
            str(e.target_arrow),
            str(e.style),
        )
        uniq[k] = e

    edges = sorted(
        uniq.values(),
        key=lambda e: (
            e.kind,
            e.src.node.name,
            e.src.row or "",
            e.dst.node.name,
        ),
    )

    return tables, edges


# ============================================================
# D2 emission
# ============================================================


def render_d2(
    roots: Iterable[type[BaseModel]],
    *,
    direction: str | None = "right",
    include_inherited_rows: bool = True,
    qualified_names: bool = False,
    include_docstrings: bool = True,
    shorten_type_names: bool = True,
    show_inheritance: bool = True,
    show_composition: bool = True,
) -> str:
    """
    Render D2 code for the provided root model classes.

    Args:
        roots: Root model classes
        direction: D2 layout direction (right, down, etc.)
        include_inherited_rows: Show inherited fields in subclasses
        qualified_names: Use module.ClassName for collision avoidance
        shorten_type_names: Shorten type names to avoid collisions
        show_inheritance: Show inheritance relationships
        show_composition: Show composition relationships
    Returns:
        D2 code as a string

    Note: shorten_type_names works best with the `typenames` library installed.
    Without it, domain types may appear with simple names only.
    """
    tables, edges = build_graph(
        roots,
        include_inherited_rows=include_inherited_rows,
        qualified_names=qualified_names,
        include_docstrings=include_docstrings,
        shorten_type_names=shorten_type_names,
        show_inheritance=show_inheritance,
        show_composition=show_composition,
    )
    w = D2Writer()

    if direction:
        w.line(f"direction: {direction}")
        w.line()

    # Tables
    for t in sorted(tables, key=lambda x: x.node.name):
        w.block_start(d2_id(t.node.name))
        w.line("shape: sql_table")

        # Add tooltip from docstring
        if include_docstrings:
            docstring = _get_model_docstring(t.node.model)
            if docstring:
                w.line(f"tooltip: {_d2_quote(docstring)}")

        for r in t.rows:
            row_key = d2_id(r.name)
            rhs = _d2_quote(r.type_str)
            if r.constraint:
                w.line(
                    f"{row_key}: {rhs} {{constraint: {d2_string_value(r.constraint)}}}"
                )
            else:
                w.line(f"{row_key}: {rhs}")
        w.block_end()
        w.line()

    # Edges
    for e in edges:
        src = (
            d2_id(e.src.node.name)
            if e.src.row is None
            else f"{d2_id(e.src.node.name)}.{d2_id(e.src.row)}"
        )
        dst = (
            d2_id(e.dst.node.name)
            if e.dst.row is None
            else f"{d2_id(e.dst.node.name)}.{d2_id(e.dst.row)}"
        )

        if e.label or e.source_arrow or e.target_arrow or e.style:
            w.line(f"{src} -> {dst}: {{")
            w._level += 1
            if e.label:
                w.line(f"label: {d2_string_value(e.label)}")
            if e.source_arrow:
                w.line("source-arrowhead: {")
                w._level += 1
                _render_style_kv(w, e.source_arrow)
                w._level -= 1
                w.line("}")
            if e.target_arrow:
                w.line("target-arrowhead: {")
                w._level += 1
                _render_style_kv(w, e.target_arrow)
                w._level -= 1
                w.line("}")
            if e.style:
                w.line("style: {")
                w._level += 1
                _render_style_kv(w, e.style)
                w._level -= 1
                w.line("}")
            w._level -= 1
            w.line("}")
        else:
            w.line(f"{src} -> {dst}")

    return w.render()
```

