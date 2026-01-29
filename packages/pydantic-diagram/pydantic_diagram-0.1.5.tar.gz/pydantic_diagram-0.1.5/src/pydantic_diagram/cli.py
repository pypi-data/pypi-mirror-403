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
