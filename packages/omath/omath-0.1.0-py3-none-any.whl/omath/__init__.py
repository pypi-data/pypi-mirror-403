"""
omath - A simple math and string utilities library.

Built from first principles:
- NO external libraries
- NO standard library helpers (no str.lower, str.split, re, collections, etc.)
- Only: loops, conditionals, lists, dicts, strings, ord(), chr()

This file runs when someone does: import omath
"""

# ============================================================
# Arithmetic functions
# ============================================================
from .arithmetic import (
    add,
    subtract,
    multiply,
    divide,
    modulo,
    power,
    absolute,
    PI,
)

# ============================================================
# Geometry functions
# ============================================================
from .geometry import (
    circle_area,
    circle_circumference,
    rectangle_area,
    rectangle_perimeter,
    triangle_area,
    square_area,
    cube_volume,
)

# ============================================================
# String functions
# ============================================================
from .strings import (
    to_lowercase,
    to_uppercase,
    split_by_char,
    strip_whitespace,
    contains,
    reverse_string,
    is_palindrome,
    char_count,
)

# ============================================================
# Define what "from omath import *" exports
# ============================================================
__all__ = [
    # Arithmetic
    'add', 'subtract', 'multiply', 'divide', 'modulo', 'power', 'absolute', 'PI',
    # Geometry
    'circle_area', 'circle_circumference', 'rectangle_area', 'rectangle_perimeter',
    'triangle_area', 'square_area', 'cube_volume',
    # Strings
    'to_lowercase', 'to_uppercase', 'split_by_char', 'strip_whitespace',
    'contains', 'reverse_string', 'is_palindrome', 'char_count',
]

# ============================================================
# Package metadata
# ============================================================
__version__ = '0.1.0'
__author__ = 'Om Mishra'
