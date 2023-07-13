from __future__ import annotations

import pytest

from unkey import _fix


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param("filter(None, d.keys())", "filter(None, d)", id="filter attr"),
        pytest.param(
            "filter(None, {}.keys())", "filter(None, {})", id="filter literal"
        ),
        pytest.param("filter(None, f().keys())", "filter(None, f())", id="filter func"),
        pytest.param(
            "map(lambda x: x * 2, d.keys())", "map(lambda x: x * 2, d)", id="map attr"
        ),
        pytest.param(
            "map(lambda x: x * 2, {}.keys())",
            "map(lambda x: x * 2, {})",
            id="map literal",
        ),
        pytest.param(
            "map(lambda x: x * 2, f().keys())",
            "map(lambda x: x * 2, f())",
            id="map func",
        ),
    ),
)
def test_zip(s, expected):
    assert _fix(s) == expected


@pytest.mark.parametrize(
    "s",
    (
        pytest.param("filter(None, [1, 2, 3])", id="filter no keys"),
        pytest.param("map(lambda x: x * 2, [1, 2, 3])", id="map no keys"),
    ),
)
def test_zip_noop(s):
    assert _fix(s) == s
