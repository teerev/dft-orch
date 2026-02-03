import pytest

from calculator import Calculator


def test_add_subtract_multiply():
    c = Calculator()
    assert c.add(2, 3) == 5
    assert c.subtract(10, 4) == 6
    assert c.multiply(6, 7) == 42


def test_apowerb_and_divide():
    c = Calculator()
    assert c.apowerb(2, 5) == 32
    assert c.divide(9, 3) == 3


def test_divide_by_zero_raises_value_error():
    c = Calculator()
    with pytest.raises(ValueError):
        c.divide(1, 0)
