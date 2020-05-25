import argparse
import ast
import re
import sys
import tokenize
import warnings
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Union

from tokenize_rt import Offset
from tokenize_rt import reversed_enumerate
from tokenize_rt import src_to_tokens
from tokenize_rt import Token
from tokenize_rt import tokens_to_src
from tokenize_rt import UNIMPORTANT_WS

BRACES = {"(": ")", "[": "]", "{": "}"}
RE_KEYS = re.compile(r"\.keys\(\s*\)$")


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
    SIMPLE_BUILTINS = frozenset(
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

    LOOKALIKES = SIMPLE_BUILTINS | frozenset(("filter", "join", "zip"))

    def __init__(self) -> None:
        self.builtin_calls: Set[Offset] = set()
        self.join_calls: Set[Offset] = set()
        self.filter_calls: Set[Offset] = set()
        self.zip_calls: Set[Offset] = set()
        self.comparison_ins: Set[Offset] = set()
        self.comprehension_ins: Set[Offset] = set()

        self.lookalikes: Set[str] = set()

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        self.lookalikes.update(
            n
            for n in (name.asname or name.name for name in node.names)
            if n in self.LOOKALIKES
        )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in self.SIMPLE_BUILTINS
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Call)
            and isinstance(node.args[0].func, ast.Attribute)
            and node.args[0].func.attr == "keys"
            and not node.args[0].args
            and not node.args[0].keywords
        ):
            self.builtin_calls.add(_ast_to_offset(node))
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Call)
            and isinstance(node.args[0].func, ast.Attribute)
            and node.args[0].func.attr == "keys"
            and not node.args[0].args
            and not node.args[0].keywords
        ):
            self.join_calls.add(_ast_to_offset(node))
        elif (
            isinstance(node.func, ast.Name)
            and node.func.id == "filter"
            and len(node.args) == 2
            and isinstance(node.args[1], ast.Call)
            and isinstance(node.args[1].func, ast.Attribute)
            and node.args[1].func.attr == "keys"
            and not node.args[1].args
            and not node.args[1].keywords
        ):
            self.filter_calls.add(_ast_to_offset(node))
        elif (
            isinstance(node.func, ast.Name)
            and node.func.id == "zip"
            and any(
                (
                    isinstance(arg, ast.Call)
                    and isinstance(arg.func, ast.Attribute)
                    and isinstance(arg.func.value, (ast.Name, ast.Dict, ast.Call))
                    and arg.func.attr == "keys"
                    and not arg.args
                    and not arg.keywords
                )
                for arg in node.args
            )
        ):
            self.zip_calls.add(_ast_to_offset(node.func))

        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        if (
            len(node.ops) == 1
            and isinstance(node.ops[0], ast.In)
            and len(node.comparators) == 1
            and isinstance(node.comparators[0], ast.Call)
            and isinstance(node.comparators[0].func, ast.Attribute)
            and (
                isinstance(node.comparators[0].func.value, (ast.Name, ast.Dict))
                or (
                    isinstance(node.comparators[0].func.value, ast.Call)
                    and isinstance(node.comparators[0].func.value.func, ast.Name)
                    and not node.comparators[0].func.value.args
                    and not node.comparators[0].func.value.keywords
                )
            )
            and node.comparators[0].func.attr == "keys"
            and not node.comparators[0].args
            and not node.comparators[0].keywords
        ):
            self.comparison_ins.add(_ast_to_offset(node.comparators[0].func))
        self.generic_visit(node)

    def _visit_comp(
        self, node: Union[ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp]
    ) -> None:
        self.comprehension_ins.update(
            _ast_to_offset(cmp.iter.func)
            for cmp in node.generators
            if (
                isinstance(cmp.iter, ast.Call)
                and isinstance(cmp.iter.func, ast.Attribute)
                and (
                    isinstance(cmp.iter.func.value, (ast.Name, ast.Dict))
                    or (
                        isinstance(cmp.iter.func.value, ast.Call)
                        and isinstance(cmp.iter.func.value.func, ast.Name)
                        and not cmp.iter.func.value.args
                        and not cmp.iter.func.value.keywords
                    )
                )
                and cmp.iter.func.attr == "keys"
                and not cmp.iter.args
                and not cmp.iter.keywords
            )
        )

        self.generic_visit(node)

    visit_ListComp = visit_SetComp = _visit_comp
    visit_DictComp = visit_GeneratorExp = _visit_comp


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


# vendored from asottile/pyupgrade@06444be5513ab77a149b7b4ae44d51803561e36f
def _parse_call_args(tokens: List[Token], i: int) -> Tuple[List[Tuple[int, int]], int]:
    args = []
    stack = [i]
    i += 1
    arg_start = i

    while stack:
        token = tokens[i]

        if len(stack) == 1 and token.src == ",":
            args.append((arg_start, i))
            arg_start = i + 1
        elif token.src in BRACES:
            stack.append(i)
        elif token.src == BRACES[tokens[stack[-1]].src]:
            stack.pop()
            # if we're at the end, append that argument
            if not stack and tokens_to_src(tokens[arg_start:i]).strip():
                args.append((arg_start, i))

        i += 1

    return args, i


def _fix(contents_text: str) -> str:
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    visitor = Finder()
    visitor.visit(ast_obj)
    if not any(
        (
            visitor.builtin_calls,
            visitor.join_calls,
            visitor.filter_calls,
            visitor.zip_calls,
            visitor.comparison_ins,
            visitor.comprehension_ins,
        )
    ):
        return contents_text

    try:
        tokens = src_to_tokens(contents_text)
    except tokenize.TokenError:  # pragma: no cover (bpo-2180)
        return contents_text

    _fixup_dedent_tokens(tokens)

    for i, token in reversed_enumerate(tokens):
        if not token.src or token.src in visitor.lookalikes:
            continue
        elif (
            token.offset in visitor.builtin_calls or token.offset in visitor.join_calls
        ):
            j = _find_token(tokens, i, "(")
            func_args, _ = _parse_call_args(tokens, j)
            start, end = func_args[0]
            src = tokens_to_src(tokens[start:end])
            m = RE_KEYS.search(src)
            assert m is not None
            tokens[start:end] = [Token("CODE", src[: m.start()])]
        elif token.offset in visitor.filter_calls:
            j = _find_token(tokens, i, "(")
            func_args, _ = _parse_call_args(tokens, j)
            start, end = func_args[1]
            src = tokens_to_src(tokens[start:end])
            m = RE_KEYS.search(src)
            assert m is not None
            tokens[start:end] = [Token("CODE", src[: m.start()])]
        elif token.offset in visitor.zip_calls:
            j = _find_token(tokens, i, "(")
            func_args, _ = _parse_call_args(tokens, j)
            for start, end in reversed(func_args):
                src = tokens_to_src(tokens[start:end])
                m = RE_KEYS.search(src)
                if m:
                    tokens[start:end] = [Token("CODE", src[: m.start()])]
        elif (
            token.offset in visitor.comparison_ins
            or token.offset in visitor.comprehension_ins
        ):
            j = _find_token(tokens, _find_token(tokens, i, "keys"), ")")
            src = tokens_to_src(tokens[i : j + 1])
            m = RE_KEYS.search(src)
            assert m is not None
            tokens[i : j + 1] = [Token("CODE", src[: m.start()])]

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
