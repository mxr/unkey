import pytest

from unkey import _fix
from unkey import Finder


@pytest.mark.parametrize("func", Finder.BUILTINS)
def test_builtins(func):
    s = f"{func}(d().keys())"
    assert _fix(s) == f"{func}(d())"


def test_builtins_brace_counting():
    s = "min(d((1, 2)).keys())"
    assert _fix(s) == "min(d((1, 2)))"
