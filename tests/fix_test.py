import pytest

from unkey import _fix


@pytest.mark.parametrize("s", (pytest.param("x=", id="SyntaxError"),))
def test_fix_noop(s):
    assert _fix(s) == s
