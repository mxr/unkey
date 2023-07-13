from __future__ import annotations

import pytest

from unkey import _fix


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param("x in d.keys()", "x in d", id="attr"),
        pytest.param("x in {}.keys()", "x in {}", id="literal"),
        pytest.param("x in f().keys()", "x in f()", id="func"),
    ),
)
def test_in(s, expected):
    assert _fix(s) == expected


@pytest.mark.parametrize(
    "s",
    (
        pytest.param("x in f(1, 2, 3).keys()", id="func with args"),
        pytest.param("x in d1().x.y().keys()", id="complex"),
    ),
)
def test_in_noop(s):
    # don't have a great way to detect these
    assert _fix(s) == s
