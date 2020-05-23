import pytest

from unkey import _fix
from unkey import Finder


@pytest.mark.parametrize("func", Finder.BUILTINS)
def test_builtins(func):
    s = f"{func}(d.keys())"
    assert _fix(s) == f"{func}(d)"


def test_builtins_whitespace():
    s = "min(d.keys(\n))"
    assert _fix(s) == "min(d)"


def test_builtins_dedent_coverage():
    s = (
        "if True:\n"
        "    if True:\n"
        "        min(d.keys())\n"
        "    else:\n"
        "        pass\n"
    )

    # fmt:off
    expected = (
        "if True:\n"
        "    if True:\n"
        "        min(d)\n"
        "    else:\n"
        "        pass\n"
    )
    # fmt:on

    assert _fix(s) == expected


@pytest.mark.parametrize(
    "s",
    (
        pytest.param("filter(None, d.keys())", id="filter"),
        pytest.param("zip(d1.keys(), d2.keys())", id="zip"),
        pytest.param("min(d.keys(), key=lambda x: abs(x))", id="additional args"),
        pytest.param("min(d1.keys)", id="not keys func"),
        pytest.param("min(d1.keys(1,2,3))", id="keys with arg"),
        pytest.param("min(d1().x.keys())", id="complex internals"),
    ),
)
def test_builtins_noop(s):
    assert _fix(s) == s
