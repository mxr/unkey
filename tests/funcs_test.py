from __future__ import annotations

import pytest

from unkey import _fix
from unkey import Finder


@pytest.mark.parametrize("func", Finder.SIMPLE_BUILTINS)
def test_builtins(func):
    s = f"{func}(f().keys())"
    assert _fix(s) == f"{func}(f())"


def test_builtins_brace_counting():
    s = "min(d((1, 2)).keys())"
    assert _fix(s) == "min(d((1, 2)))"
