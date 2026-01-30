import pytest
from calculationengine import add, subtract, multiply, divide
import math

# ---------------- BASIC FUNCTIONALITY ----------------

def test_add_basic():
    assert add(2, 3) == 5


def test_subtract_basic():
    assert subtract(10, 4) == 6


def test_multiply_basic():
    assert multiply(3, 4) == 12


def test_divide_basic():
    assert divide(10, 2) == 5


# ---------------- MULTIPLE ARGUMENTS ----------------

def test_add_many():
    assert add(1, 2, 3, 4) == 10


def test_subtract_many():
    assert subtract(20, 5, 5) == 10


def test_multiply_many():
    assert multiply(2, 3, 4) == 24


def test_divide_many():
    assert divide(100, 2, 5) == 10


# ---------------- ITERABLE INPUTS ----------------

def test_add_list():
    assert add([1, 2, 3]) == 6


def test_add_tuple():
    assert add((1, 2, 3)) == 6


def test_add_range():
    assert add(range(1, 6)) == 15


def test_add_generator():
    assert add(x for x in [1, 2, 3]) == 6


# ---------------- STRING NUMBERS ----------------

def test_add_string_numbers():
    assert add("1", "2", "3") == 6


def test_add_string_floats():
    assert add("1.5", "2.5") == 4.0


def test_mixed_string_and_int():
    assert add("2", 3, "4") == 9


# ---------------- FLOATS & NEGATIVES ----------------

def test_add_floats():
    assert add(1.5, 2.5) == 4.0


def test_negative_numbers():
    assert add(-1, -2, -3) == -6


def test_mixed_positive_negative():
    assert subtract(10, -5) == 15


# ---------------- EMPTY & TOO FEW INPUTS ----------------

def test_add_no_args():
    with pytest.raises(ValueError):
        add()


def test_add_empty_list():
    with pytest.raises(ValueError):
        add([])


def test_subtract_one_arg():
    with pytest.raises(ValueError):
        subtract(5)


def test_divide_one_arg():
    with pytest.raises(ValueError):
        divide(10)


# ---------------- DIVIDE BY ZERO ----------------

def test_divide_by_zero_direct():
    with pytest.raises(ValueError):
        divide(10, 0)


def test_divide_by_zero_later():
    with pytest.raises(ValueError):
        divide(100, 2, 0)


def test_divide_zero_string():
    with pytest.raises(ValueError):
        divide("10", "0")


# ---------------- INVALID TYPES ----------------

def test_invalid_string():
    with pytest.raises(TypeError):
        add("a", "b")


def test_none_input():
    with pytest.raises(TypeError):
        add(None, 2)


def test_dict_input():
    with pytest.raises(TypeError):
        add({"a": 1})


def test_set_input():
    with pytest.raises(TypeError):
        add({1, 2, 3})


def test_list_with_invalid_value():
    with pytest.raises(TypeError):
        add([1, "a", 3])


# ---------------- BOOLEAN HANDLING ----------------

def test_bool_rejected():
    with pytest.raises(TypeError):
        add(True, 1)


def test_bool_in_list():
    with pytest.raises(TypeError):
        add([1, True, 3])


# ---------------- NESTED ITERABLES ----------------

def test_nested_list():
    with pytest.raises(TypeError):
        add([1, [2, 3]])


# ---------------- LARGE NUMBERS ----------------

def test_large_numbers():
    assert add(10**10, 10**10) == 2 * 10**10

    


# ---------------- WEIRD BUT VALID ----------------

def test_single_iterable_generator():
    gen = (x for x in range(5))
    assert add(gen) == 10


def test_string_iterable_not_split():
    with pytest.raises(TypeError):
        add("123")  # should not treat string as iterable of digits

def test_float_precision():
    assert add(0.1, 0.2) != 0.3

# ---------------- TYPE STABILITY ----------------

def test_result_type_int():
    assert isinstance(add(1, 2, 3), int)


def test_result_type_float():
    assert isinstance(add("1.5", "2.5"), float)

# ---------------- NaN & INFINITY ----------------

def test_nan_rejected():
    with pytest.raises(ValueError):
        add(math.nan, 1)


def test_infinity_rejected():
    with pytest.raises(ValueError):
        add(math.inf, 1)


def test_negative_infinity_rejected():
    with pytest.raises(ValueError):
        add(-math.inf, 1)


# ---------------- VERY LARGE NUMBERS ----------------

def test_big_integer_multiply():
    assert multiply(10**1000, 10**1000) == 10**2000


def test_float_overflow_detection():
    with pytest.raises(OverflowError):
        multiply(1e308, 1e308)


# ---------------- ITERATOR EXHAUSTION ----------------

def test_generator_exhaustion():
    gen = (x for x in [1, 2, 3])
    assert add(gen) == 6
    with pytest.raises(ValueError):
        add(gen)   # generator is now empty


# ---------------- UNICODE NUMERIC STRINGS ----------------

def test_arabic_digits():
    assert add("٣", "٤") == 7


def test_fullwidth_digits():
    assert add("２", "３") == 5


def test_hindi_digits():
    assert add("१२", "३") == 15


# ---------------- FLOAT PRECISION (DOCUMENTED BEHAVIOR) ----------------

def test_float_precision_behavior():
    # IEEE float behavior is expected, not a bug
    assert add(0.1, 0.2) != 0.3