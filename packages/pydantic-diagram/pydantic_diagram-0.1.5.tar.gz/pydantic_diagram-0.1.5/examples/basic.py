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
