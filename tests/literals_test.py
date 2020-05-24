import pytest

from unkey import _fix
from unkey import Finder


@pytest.mark.parametrize("func", Finder.SIMPLE_BUILTINS)
def test_builtins(func):
    s = f"{func}({{1: 2, 3: 4}}.keys())"
    assert _fix(s) == f"{func}({{1: 2, 3: 4}})"


def test_builtins_brace_counting():
    s = "min({1: 2, 3: {4, \n5, 6}, 7: {8: 9}}.keys())"
    assert _fix(s) == "min({1: 2, 3: {4, \n5, 6}, 7: {8: 9}})"
