import argparse
import ast
import sys
import tokenize
import warnings
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Union

from tokenize_rt import Offset
from tokenize_rt import reversed_enumerate
from tokenize_rt import src_to_tokens
from tokenize_rt import Token
from tokenize_rt import tokens_to_src
from tokenize_rt import UNIMPORTANT_WS


# vendored from asottile/pyupgrade@06444be5513ab77a149b7b4ae44d51803561e36f
def _find_token(tokens: List[Token], i: int, src: str) -> int:
    while tokens[i].src != src:
        i += 1
    return i


# vendored from asottile/pyupgrade@06444be5513ab77a149b7b4ae44d51803561e36f
def _ast_to_offset(node: Union[ast.expr, ast.stmt]) -> Offset:
    return Offset(node.lineno, node.col_offset)


# vendored from asottile/pyupgrade@06444be5513ab77a149b7b4ae44d51803561e36f
def ast_parse(contents_text: str) -> ast.Module:
    # intentionally ignore warnings, we might be fixing warning-ridden syntax
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(contents_text.encode())


class Finder(ast.NodeVisitor):
    BUILTINS = frozenset(
        (
            "all",
            "any",
            "bool",
            "bytearray",
            "bytes",
            "dict",
            "enumerate",
            "frozenset",
            "iter",
            "len",
            "list",
            "map",
            "max",
            "min",
            "next",
            "range",
            "reversed",
            "set",
            "sorted",
            "sum",
            "tuple",
        )
    )

    def __init__(self) -> None:
        self.builtin_calls: Set[Offset] = set()

    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in self.BUILTINS
            and len(node.args) == 1
            and not node.keywords
            and isinstance(node.args[0], ast.Call)
            and isinstance(node.args[0].func, ast.Attribute)
            and node.args[0].func.attr == "keys"
            and not node.args[0].args
            and not node.args[0].keywords
        ):
            self.builtin_calls.add(_ast_to_offset(node.args[0].func))
        self.generic_visit(node)


# vendored from asottile/pyupgrade@06444be5513ab77a149b7b4ae44d51803561e36f
def _fixup_dedent_tokens(tokens: List[Token]) -> None:
    """For whatever reason the DEDENT / UNIMPORTANT_WS tokens are misordered

    | if True:
    |     if True:
    |         pass
    |     else:
    |^    ^- DEDENT
    |+----UNIMPORTANT_WS
    """
    for i, token in enumerate(tokens):
        if token.name == UNIMPORTANT_WS and tokens[i + 1].name == "DEDENT":
            tokens[i], tokens[i + 1] = tokens[i + 1], tokens[i]


def _fix(contents_text: str) -> str:
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    visitor = Finder()
    visitor.visit(ast_obj)

    if not any((visitor.builtin_calls,)):
        return contents_text

    try:
        tokens = src_to_tokens(contents_text)
    except tokenize.TokenError:  # pragma: no cover (bpo-2180)
        return contents_text

    _fixup_dedent_tokens(tokens)

    for i, token in reversed_enumerate(tokens):
        if not token.src:
            continue
        elif (
            token.offset in visitor.builtin_calls
            and tokens_to_src(tokens[i + 1 : i + 4]) == ".keys("
        ):
            j = _find_token(tokens, i + 4, ")")
            del tokens[i + 1 : j + 1]

    return tokens_to_src(tokens)


def _fix_file(filename: str) -> int:
    with open(filename, "rb") as fb:
        contents_bytes = fb.read()

    try:
        contents_text = contents_bytes.decode()
    except UnicodeDecodeError:
        print(f"{filename} is non-utf-8 (not supported)")
        return 1

    fixed = _fix(contents_text)

    if contents_text != fixed:
        print(f"Rewriting {filename}", file=sys.stderr)
        with open(filename, "w", encoding="UTF-8", newline="") as f:
            f.write(fixed)
        return 1

    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)

    ret = 0
    for filename in args.filenames:
        ret |= _fix_file(filename)
    return ret


if __name__ == "__main__":
    exit(main())
