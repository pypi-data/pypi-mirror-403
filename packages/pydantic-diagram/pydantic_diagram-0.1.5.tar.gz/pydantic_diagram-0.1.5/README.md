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