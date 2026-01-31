"""
String utilities.

NO external libraries. NO standard library helpers.
NO str.lower(), str.split(), str.upper(), str.strip(), etc.
Only: loops, conditionals, lists, dicts, strings, ord(), chr(), len().
"""


def to_lowercase(s):
    """
    Convert a string to lowercase.
    Uses ord() and chr() to map A-Z to a-z.
    """
    result = []
    for char in s:
        code = ord(char)
        # A=65, Z=90 in ASCII
        # a=97, z=122 in ASCII
        # Difference is 32
        if 65 <= code <= 90:
            result.append(chr(code + 32))
        else:
            result.append(char)

    # Join without using ''.join()
    output = ''
    for char in result:
        output = output + char
    return output


def to_uppercase(s):
    """
    Convert a string to uppercase.
    Uses ord() and chr() to map a-z to A-Z.
    """
    result = []
    for char in s:
        code = ord(char)
        # a=97, z=122 in ASCII
        if 97 <= code <= 122:
            result.append(chr(code - 32))
        else:
            result.append(char)

    output = ''
    for char in result:
        output = output + char
    return output


def split_by_char(s, delimiter):
    """
    Split a string by a delimiter character.
    Returns a list of substrings.
    """
    parts = []
    current = ''

    for char in s:
        if char == delimiter:
            parts.append(current)
            current = ''
        else:
            current = current + char

    # Don't forget the last part
    parts.append(current)
    return parts


def strip_whitespace(s):
    """
    Remove leading and trailing whitespace.
    Whitespace = space (32), tab (9), newline (10), carriage return (13).
    """
    whitespace_codes = [32, 9, 10, 13]

    # Find first non-whitespace
    start = 0
    while start < len(s):
        if ord(s[start]) not in whitespace_codes:
            break
        start = start + 1

    # Find last non-whitespace
    end = len(s) - 1
    while end >= 0:
        if ord(s[end]) not in whitespace_codes:
            break
        end = end - 1

    # Build result
    if start > end:
        return ''

    result = ''
    i = start
    while i <= end:
        result = result + s[i]
        i = i + 1
    return result


def contains(haystack, needle):
    """
    Check if needle exists in haystack.
    """
    if len(needle) == 0:
        return True
    if len(needle) > len(haystack):
        return False

    # Slide window through haystack
    i = 0
    while i <= len(haystack) - len(needle):
        # Check if needle matches at position i
        match = True
        j = 0
        while j < len(needle):
            if haystack[i + j] != needle[j]:
                match = False
                break
            j = j + 1

        if match:
            return True
        i = i + 1

    return False


def reverse_string(s):
    """
    Reverse a string.
    """
    result = ''
    i = len(s) - 1
    while i >= 0:
        result = result + s[i]
        i = i - 1
    return result


def is_palindrome(s):
    """
    Check if a string is a palindrome.
    Ignores case and non-letter characters.
    """
    # Extract only letters, lowercase
    letters = ''
    for char in s:
        code = ord(char)
        # Check if it's a letter
        if 65 <= code <= 90:  # A-Z
            letters = letters + chr(code + 32)  # Convert to lowercase
        elif 97 <= code <= 122:  # a-z
            letters = letters + char

    # Compare with reverse
    return letters == reverse_string(letters)


def char_count(s):
    """
    Count occurrences of each character.
    Returns a dict.
    """
    counts = {}
    for char in s:
        if char in counts:
            counts[char] = counts[char] + 1
        else:
            counts[char] = 1
    return counts
