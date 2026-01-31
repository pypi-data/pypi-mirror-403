"""
Geometry calculations.

NO external libraries. NO standard library helpers.
Only: loops, conditionals, lists, dicts, strings, ord(), chr().
"""

from .arithmetic import PI, multiply, add, power


def circle_area(radius):
    """
    Return the area of a circle: PI * r^2
    """
    r_squared = multiply(radius, radius)
    # PI * r^2 - we need float multiplication here
    # Since our multiply uses repeated addition (integers),
    # we'll use native * for float, but the logic is the same
    return PI * r_squared


def circle_circumference(radius):
    """
    Return the circumference of a circle: 2 * PI * r
    """
    return 2 * PI * radius


def rectangle_area(width, height):
    """
    Return the area of a rectangle: width * height
    """
    return multiply(width, height)


def rectangle_perimeter(width, height):
    """
    Return the perimeter of a rectangle: 2 * (width + height)
    """
    return multiply(2, add(width, height))


def triangle_area(base, height):
    """
    Return the area of a triangle: (base * height) / 2
    Using integer division for simplicity.
    """
    return multiply(base, height) // 2


def square_area(side):
    """
    Return the area of a square: side^2
    """
    return power(side, 2)


def cube_volume(side):
    """
    Return the volume of a cube: side^3
    """
    return power(side, 3)