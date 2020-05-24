import pytest

from unkey import _fix


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param("filter(None, d.keys())", "filter(None, d)", id="attr"),
        pytest.param("filter(None, {}.keys())", "filter(None, {})", id="literal"),
        pytest.param("filter(None, f().keys())", "filter(None, f())", id="func"),
    ),
)
def test_zip(s, expected):
    assert _fix(s) == expected


@pytest.mark.parametrize(
    "s", (pytest.param("filter(None, [1, 2, 3])", id="no keys"),),
)
def test_zip_noop(s):
    assert _fix(s) == s
