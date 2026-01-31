# omath

A Python library built from first principles for educational purposes.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![No Dependencies](https://img.shields.io/badge/dependencies-none-green.svg)](#philosophy)

## Philosophy

This library intentionally avoids:
- External dependencies
- Standard library helpers (`str.lower()`, `str.split()`, `re`, `collections`, `itertools`)
- Built-in shortcuts

Everything is implemented using only:
- Loops and conditionals
- Lists and dicts
- Strings
- `ord()` and `chr()`

**Why?** To understand how things work at the lowest level. Every function in this library could be a teaching moment.

---

## Installation

### From PyPI

```bash
pip install omath
```

### From GitHub

```bash
pip install git+https://github.com/OmMishra16/omath.git
```

### From Source

```bash
git clone https://github.com/OmMishra16/omath.git
cd omath
pip install -e .
```

---

## Quick Start

```python
import omath

# Arithmetic
result = omath.multiply(7, 8)  # 56 (uses repeated addition internally)

# Geometry
area = omath.circle_area(5)  # 78.53975

# Strings
lower = omath.to_lowercase("HELLO")  # "hello" (uses ord/chr, not str.lower)
```

---

## API Reference

### Arithmetic Module

All arithmetic operations are implemented from first principles:
- `multiply()` uses repeated addition
- `divide()` uses repeated subtraction
- `power()` uses repeated multiplication

#### `add(a, b)`

Returns the sum of two numbers.

```python
>>> omath.add(10, 5)
15
>>> omath.add(-3, 7)
4
```

#### `subtract(a, b)`

Returns the difference of two numbers.

```python
>>> omath.subtract(10, 3)
7
>>> omath.subtract(5, 8)
-3
```

#### `multiply(a, b)`

Returns the product of two numbers using repeated addition.

```python
>>> omath.multiply(7, 8)
56
>>> omath.multiply(-4, 5)
-20
>>> omath.multiply(0, 100)
0
```

**How it works internally:**
```
multiply(3, 4) = 3 + 3 + 3 + 3 = 12
```

#### `divide(a, b)`

Returns the integer quotient of a / b using repeated subtraction.

```python
>>> omath.divide(20, 4)
5
>>> omath.divide(17, 5)
3
>>> omath.divide(100, 7)
14
>>> omath.divide(10, 0)
None  # Division by zero returns None
```

**How it works internally:**
```
divide(17, 5):
  17 - 5 = 12 (count: 1)
  12 - 5 = 7  (count: 2)
  7 - 5 = 2   (count: 3)
  2 < 5, stop
  Result: 3
```

#### `modulo(a, b)`

Returns the remainder of a / b.

```python
>>> omath.modulo(17, 5)
2
>>> omath.modulo(100, 7)
2
>>> omath.modulo(10, 0)
None  # Modulo by zero returns None
```

#### `power(base, exponent)`

Returns base raised to exponent (non-negative integers only).

```python
>>> omath.power(2, 10)
1024
>>> omath.power(5, 3)
125
>>> omath.power(7, 0)
1
>>> omath.power(2, -1)
None  # Negative exponents not supported
```

**How it works internally:**
```
power(2, 4) = multiply(multiply(multiply(1, 2), 2), 2), 2)
            = 1 * 2 * 2 * 2 * 2 = 16
```

#### `absolute(n)`

Returns the absolute value of n.

```python
>>> omath.absolute(-42)
42
>>> omath.absolute(42)
42
>>> omath.absolute(0)
0
```

#### `PI`

A constant approximation of pi (3.14159).

```python
>>> omath.PI
3.14159
```

---

### Geometry Module

Functions for calculating areas, perimeters, and volumes.

#### `circle_area(radius)`

Returns the area of a circle (PI * r^2).

```python
>>> omath.circle_area(5)
78.53975
>>> omath.circle_area(1)
3.14159
>>> omath.circle_area(10)
314.159
```

#### `circle_circumference(radius)`

Returns the circumference of a circle (2 * PI * r).

```python
>>> omath.circle_circumference(5)
31.4159
>>> omath.circle_circumference(1)
6.28318
```

#### `rectangle_area(width, height)`

Returns the area of a rectangle.

```python
>>> omath.rectangle_area(4, 5)
20
>>> omath.rectangle_area(10, 10)
100
```

#### `rectangle_perimeter(width, height)`

Returns the perimeter of a rectangle (2 * (width + height)).

```python
>>> omath.rectangle_perimeter(4, 5)
18
>>> omath.rectangle_perimeter(10, 10)
40
```

#### `triangle_area(base, height)`

Returns the area of a triangle (base * height / 2).

```python
>>> omath.triangle_area(10, 5)
25
>>> omath.triangle_area(8, 6)
24
```

#### `square_area(side)`

Returns the area of a square (side^2).

```python
>>> omath.square_area(5)
25
>>> omath.square_area(12)
144
```

#### `cube_volume(side)`

Returns the volume of a cube (side^3).

```python
>>> omath.cube_volume(3)
27
>>> omath.cube_volume(5)
125
```

---

### Strings Module

All string operations are implemented using `ord()` and `chr()` — no built-in string methods like `str.lower()` or `str.split()`.

#### `to_lowercase(s)`

Converts a string to lowercase using ASCII math.

```python
>>> omath.to_lowercase("HELLO WORLD")
'hello world'
>>> omath.to_lowercase("PyThOn")
'python'
>>> omath.to_lowercase("123 ABC")
'123 abc'
```

**How it works internally:**
```
'A' = chr(65), 'a' = chr(97)
Difference = 32
So: chr(ord('A') + 32) = 'a'
```

#### `to_uppercase(s)`

Converts a string to uppercase using ASCII math.

```python
>>> omath.to_uppercase("hello world")
'HELLO WORLD'
>>> omath.to_uppercase("PyThOn")
'PYTHON'
```

#### `split_by_char(s, delimiter)`

Splits a string by a delimiter character.

```python
>>> omath.split_by_char("a,b,c,d", ",")
['a', 'b', 'c', 'd']
>>> omath.split_by_char("hello world", " ")
['hello', 'world']
>>> omath.split_by_char("one-two-three", "-")
['one', 'two', 'three']
```

#### `strip_whitespace(s)`

Removes leading and trailing whitespace (spaces, tabs, newlines).

```python
>>> omath.strip_whitespace("  hello  ")
'hello'
>>> omath.strip_whitespace("\t\n  text  \n\t")
'text'
>>> omath.strip_whitespace("no_whitespace")
'no_whitespace'
```

#### `contains(haystack, needle)`

Checks if needle exists in haystack.

```python
>>> omath.contains("hello world", "world")
True
>>> omath.contains("hello world", "xyz")
False
>>> omath.contains("abcdef", "cde")
True
>>> omath.contains("short", "very long string")
False
```

#### `reverse_string(s)`

Reverses a string.

```python
>>> omath.reverse_string("hello")
'olleh'
>>> omath.reverse_string("Python")
'nohtyP'
>>> omath.reverse_string("12345")
'54321'
```

#### `is_palindrome(s)`

Checks if a string is a palindrome (ignores case and non-letter characters).

```python
>>> omath.is_palindrome("racecar")
True
>>> omath.is_palindrome("A man a plan a canal Panama")
True
>>> omath.is_palindrome("hello")
False
>>> omath.is_palindrome("Was it a car or a cat I saw")
True
```

#### `char_count(s)`

Counts occurrences of each character in a string.

```python
>>> omath.char_count("hello")
{'h': 1, 'e': 1, 'l': 2, 'o': 1}
>>> omath.char_count("aaa")
{'a': 3}
>>> omath.char_count("abab")
{'a': 2, 'b': 2}
```

---

## Submodule Access

You can also import submodules directly:

```python
# Import specific module
from omath import arithmetic
from omath import geometry
from omath import strings

# Use functions
arithmetic.multiply(5, 5)
geometry.circle_area(10)
strings.reverse_string("test")
```

Or import specific functions:

```python
from omath import add, multiply, power
from omath import circle_area, rectangle_area
from omath import to_lowercase, is_palindrome

result = multiply(add(2, 3), power(2, 3))  # (2+3) * 2^3 = 40
```

---

## Educational Value

This library is designed to help you understand:

1. **How multiplication works** — It's just repeated addition
2. **How division works** — It's just repeated subtraction
3. **How string methods work** — ASCII codes and character manipulation
4. **How Python packages work** — Module structure, `__init__.py`, imports

### Example: Understanding `to_lowercase()`

Instead of using `str.lower()`, we use ASCII math:

```python
def to_lowercase(s):
    result = ''
    for char in s:
        code = ord(char)
        # A-Z are 65-90, a-z are 97-122
        # Difference is 32
        if 65 <= code <= 90:
            result = result + chr(code + 32)
        else:
            result = result + char
    return result
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**Om Mishra** - [GitHub](https://github.com/OmMishra16)
