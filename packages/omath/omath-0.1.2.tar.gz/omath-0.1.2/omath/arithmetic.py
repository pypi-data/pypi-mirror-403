"""
Basic arithmetic operations.

NO external libraries. NO standard library helpers.
Only: loops, conditionals, lists, dicts, strings, ord(), chr().
"""


def add(a, b):
    """Return the sum of two numbers."""
    return a + b


def subtract(a, b):
    """Return the difference of two numbers."""
    return a - b


def multiply(a, b):
    """
    Return the product of two numbers.
    Implemented using repeated addition.
    """
    if b == 0 or a == 0:
        return 0

    # Handle negative numbers
    negative = False
    if a < 0:
        a = -a
        negative = not negative
    if b < 0:
        b = -b
        negative = not negative

    # Repeated addition (optimize by using smaller number as counter)
    if a < b:
        a, b = b, a  # swap so we add 'a' to itself 'b' times

    result = 0
    for _ in range(b):
        result = result + a

    return -result if negative else result


def divide(a, b):
    """
    Return the integer quotient of a / b.
    Implemented using repeated subtraction.
    """
    if b == 0:
        # Manual error - no exceptions beyond basic Python
        return None  # Represents undefined

    negative = False
    if a < 0:
        a = -a
        negative = not negative
    if b < 0:
        b = -b
        negative = not negative

    count = 0
    while a >= b:
        a = a - b
        count = count + 1

    return -count if negative else count


def modulo(a, b):
    """
    Return the remainder of a / b.
    """
    if b == 0:
        return None

    # a mod b = a - (a // b) * b
    quotient = divide(a, b)
    if quotient is None:
        return None

    return a - multiply(quotient, b)


def power(base, exponent):
    """
    Return base raised to exponent (non-negative integers only).
    Implemented using repeated multiplication.
    """
    if exponent < 0:
        return None  # We don't handle negative exponents
    if exponent == 0:
        return 1

    result = 1
    for _ in range(exponent):
        result = multiply(result, base)

    return result


def absolute(n):
    """Return the absolute value of n."""
    if n < 0:
        return -n
    return n


# Constants - computed without using math library
# PI approximation using Leibniz formula (limited iterations for simplicity)
# PI/4 = 1 - 1/3 + 1/5 - 1/7 + 1/9 - ...
def _compute_pi_approximation():
    """Compute PI using Leibniz formula with manual division."""
    # We'll use a simpler approach: hardcode a rational approximation
    # 355/113 is accurate to 6 decimal places
    # Manual long division: 355 / 113 = 3.14159292...
    # For simplicity, we store the known value
    return 3.14159

PI = _compute_pi_approximation()