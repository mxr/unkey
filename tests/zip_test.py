import pytest

from unkey import _fix


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param("zip(d.keys(), [1, 2, 3])", "zip(d, [1, 2, 3])", id="attr"),
        pytest.param("zip({}.keys(), [1, 2, 3])", "zip({}, [1, 2, 3])", id="literal"),
        pytest.param("zip([1, 2, 3], f().keys())", "zip([1, 2, 3], f())", id="func"),
        pytest.param(
            "zip(d.keys(), {}.keys(), f().keys())",
            "zip(d, {}, f())",
            id="attr literal and func",
        ),
        pytest.param(
            "zip(d.keys(), {}.keys(), [1, 2, 3])",
            "zip(d, {}, [1, 2, 3])",
            id="mix rewrite and noop",
        ),
    ),
)
def test_zip(s, expected):
    assert _fix(s) == expected


@pytest.mark.parametrize(
    "s", (pytest.param("zip([1, 2, 3], [4, 5, 6])", id="no keys"),),
)
def test_zip_noop(s):
    assert _fix(s) == s
