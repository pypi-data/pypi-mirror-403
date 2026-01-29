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
