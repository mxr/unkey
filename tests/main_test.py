from __future__ import annotations

import pytest

from unkey import main


@pytest.mark.parametrize(
    ("s", "expected"),
    (
        pytest.param(b"", 0, id="no content"),
        pytest.param(b"x =", 0, id="SyntaxError"),
        pytest.param(
            "# -*- coding: cp1252 -*-\nx = €\n".encode("cp1252"), 1, id="non-utf-8"
        ),
        pytest.param(b"min(d.keys())", 1, id="rewrite"),
    ),
)
def test_main(tmpdir, s, expected):
    f = tmpdir.join("f.py")
    f.write_binary(s)
    assert main((str(f),)) == expected
