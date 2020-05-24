import pytest

from unkey import _fix
from unkey import Finder


@pytest.mark.parametrize("func", Finder.SIMPLE_BUILTINS)
def test_builtins(func):
    s = f"{func}(d.keys())"
    assert _fix(s) == f"{func}(d)"


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param("min(d.keys(\n))", "min(d)", id="whitespace"),
        pytest.param(
            "min(d1().x.y().keys())", "min(d1().x.y())", id="complex internals"
        ),
        pytest.param(
            "min(d.keys(), key=lambda x: -x)",
            "min(d, key=lambda x: -x)",
            id="min kwargs",
        ),
        pytest.param(
            "sorted(d.keys(), key=lambda x: -x, reverse=True)",
            "sorted(d, key=lambda x: -x, reverse=True)",
            id="sorted kwargs",
        ),
    ),
)
def test_builtins_complex(s, expected):
    assert _fix(s) == expected


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
        pytest.param("min(d1.keys)", id="not keys func"),
        pytest.param("min(d1.keys(1,2,3))", id="keys with arg"),
        pytest.param("foo.min(d.keys())", id="not builtin min - instance method"),
        pytest.param(
            "from foo import min\n\nmin(d.keys())", id="not builtin min - import"
        ),
        pytest.param(
            "from foo import min2 as min\n\nmin(d.keys())",
            id="not builtin min - import with asname",
        ),
    ),
)
def test_builtins_noop(s):
    assert _fix(s) == s
