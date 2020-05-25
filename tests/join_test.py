import pytest

from unkey import _fix


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param("''.join(d.keys())", "''.join(d)", id="attr"),
        pytest.param("''.join({}.keys())", "''.join({})", id="literal"),
        pytest.param("''.join(f().keys())", "''.join(f())", id="func"),
        pytest.param("''.join(d1().x.y().keys())", "''.join(d1().x.y())", id="complex"),
    ),
)
def test_join(s, expected):
    assert _fix(s) == expected
