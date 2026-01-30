from functools import reduce
import operator
from numbers import Number
import math
import unicodedata


def _parse_string_number(s: str):
    """
    Convert string to number.
    Supports:
      "10", "1.5"
      "٣" (Arabic digit)
      "２" (fullwidth digit)
    """

    # Try normal int/float first
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        pass

    # Try Unicode numeric characters (like Arabic, fullwidth)
    try:
        digits = []
        for ch in s:
            val = unicodedata.numeric(ch)
            digits.append(str(int(val)))
        return int("".join(digits))
    except Exception:
        raise TypeError(f"Invalid numeric string: {s}")


def _flatten_inputs(*args):
    """
    Rules:
      - At least TWO operands required
      - Accepts numbers, numeric strings, list/tuple/range/generator
      - Rejects dict, set, bool
      - Rejects NaN and Infinity
      - Supports Unicode numeric strings
    """

    if len(args) == 0:
        raise ValueError("At least two numbers are required")

    # Reject dict
    if len(args) == 1 and isinstance(args[0], dict):
        raise TypeError("Dictionary input is not supported")

    # Reject set
    if len(args) == 1 and isinstance(args[0], set):
        raise TypeError("Set input is not supported")

    # Reject single string
    if len(args) == 1 and isinstance(args[0], str):
        raise TypeError("Single string input is not allowed")

    # Expand single iterable (but not string/bytes)
    if len(args) == 1 and not isinstance(args[0], (str, bytes)) and hasattr(args[0], "__iter__"):
        values = list(args[0])
    else:
        values = list(args)

    if len(values) < 2:
        raise ValueError("At least two numbers are required")

    normalized = []
    for v in values:
        # Reject bool
        if isinstance(v, bool):
            raise TypeError("Boolean values are not allowed")

        # Accept numbers
        if isinstance(v, Number):
            # Reject NaN / Infinity
            if isinstance(v, float) and not math.isfinite(v):
                raise ValueError("NaN and Infinity are not allowed")
            normalized.append(v)
            continue

        # Convert numeric strings
        if isinstance(v, str):
            num = _parse_string_number(v)
            if isinstance(num, float) and not math.isfinite(num):
                raise ValueError("NaN and Infinity are not allowed")
            normalized.append(num)
            continue

        raise TypeError(f"Unsupported input type: {type(v).__name__}")

    return normalized


def add(*args):
    nums = _flatten_inputs(*args)
    return sum(nums)


def subtract(*args):
    nums = _flatten_inputs(*args)
    return reduce(operator.sub, nums)


def multiply(*args):
    nums = _flatten_inputs(*args)
    result = 1
    for n in nums:
        result *= n
        # protect against float overflow to inf
        if isinstance(result, float) and not math.isfinite(result):
            raise OverflowError("Result overflowed to infinity")
    return result


def divide(*args):
    nums = _flatten_inputs(*args)
    result = nums[0]
    for n in nums[1:]:
        if n == 0:
            raise ValueError("Cannot divide by zero")
        result /= n
        if isinstance(result, float) and not math.isfinite(result):
            raise OverflowError("Result overflowed to infinity")
    return result
