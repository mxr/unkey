from __future__ import annotations

import pytest

from unkey import _fix


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param("for i in d.keys(): pass", "for i in d: pass", id="attr"),
        pytest.param("for i in {}.keys(): pass", "for i in {}: pass", id="literal"),
        pytest.param("for i in f().keys(): pass", "for i in f(): pass", id="func"),
    ),
)
def test_for(s, expected):
    assert _fix(s) == expected


@pytest.mark.parametrize(
    ("s",),
    (pytest.param("for i in []: pass", id="not dict"),),
)
def test_for_noop(s):
    assert _fix(s) == s
