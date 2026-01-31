"""Red Dragon Package

A Python package that awakens the red dragon!
"""

__version__ = "0.1.1"
__author__ = "karzimeg"

from .cli import print_dragon_fallback, print_new_dragon

print("red-dragon package installed, type 'red-dragon' to use")

__all__ = ["print_dragon_fallback", "print_new_dragon"]
