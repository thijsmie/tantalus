import pytest

from holdmybeer import argsort_by_fraction, divide


def test_argsort_by_fraction():
    fractions = [0.0, 1.111, 2.011, 18.01]
    order = argsort_by_fraction(fractions)
    
    assert [1, 2, 3, 0] == order


def test_divide():
    ratios = [1, 2, 4, 8]
    division = divide(15, ratios)
    
    assert ratios == division
    
    division = divide(14, ratios)
    
    assert [1, 2, 4, 7] == division
    
    division = divide(8, ratios)
    
    assert [1, 1, 2, 4] == division
