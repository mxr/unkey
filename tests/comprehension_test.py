import pytest

from unkey import _fix


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param("[x for x in d.keys()]", "[x for x in d]", id="attr list comp"),
        pytest.param(
            "[x for x in {}.keys()]", "[x for x in {}]", id="literal list comp"
        ),
        pytest.param(
            "[x for x in f().keys()]", "[x for x in f()]", id="func list comp"
        ),
        pytest.param("(x for x in d.keys())", "(x for x in d)", id="attr gen exp"),
        pytest.param("(x for x in {}.keys())", "(x for x in {})", id="literal gen exp"),
        pytest.param("(x for x in f().keys())", "(x for x in f())", id="func gen exp"),
        pytest.param("{x for x in d.keys()}", "{x for x in d}", id="attr set comp"),
        pytest.param(
            "{x for x in {}.keys()}", "{x for x in {}}", id="literal set comp"
        ),
        pytest.param("{x for x in f().keys()}", "{x for x in f()}", id="func set comp"),
        pytest.param(
            "{x:x for x in d.keys()}", "{x:x for x in d}", id="attr dict comp"
        ),
        pytest.param(
            "{x:x for x in {}.keys()}", "{x:x for x in {}}", id="literal dict comp"
        ),
        pytest.param(
            "{x:x for x in f().keys()}", "{x:x for x in f()}", id="func dict comp"
        ),
    ),
)
def test_comprehensions(s, expected):
    assert _fix(s) == expected
