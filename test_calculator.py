import pytest

from calculator import Calculator


def test_add():
    c = Calculator()
    assert c.add(2, 3) == 5


def test_subtract():
    c = Calculator()
    assert c.subtract(10, 4) == 6


def test_apowerb():
    c = Calculator()
    assert c.apowerb(2, 3) == 8


def test_multiply():
    c = Calculator()
    assert c.multiply(6, 7) == 42


def test_divide():
    c = Calculator()
    assert c.divide(10, 4) == 2.5


def test_divide_by_zero_raises_value_error():
    c = Calculator()
    with pytest.raises(ValueError):
        c.divide(1, 0)
