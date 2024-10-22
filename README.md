# `unkey`

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/mxr/unkey/main.svg)](https://results.pre-commit.ci/latest/github/mxr/unkey/main)

A tool and pre-commit hook to automatically remove extra calls to `keys()`.

## Installation

`pip install unkey`

## As a pre-commit hook

See [pre-commit][pre-commit] for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/mxr/unkey
    rev: v0.0.2
    hooks:
    -   id: unkey
```

## Overview

### Summary

Iterating over a Python dictionary will iterate over its keys, so calls to
`keys()` are often not needed. Removing these calls keeps your code terser and
more readable.

### Excluding Code

`unkey` does not support an equivalent of flake8's `# noqa` or mypy's  `#type:
ignore` to stop rewriting. Until this feature is available, use  an intermediate
variable to prevent rewriting.

```python
# will be rewritten
min({1: 2, 3: 4}.keys())  # becomes min({1: 2, 3: 4})

# will not be rewritten
keys = {1: 2, 3: 4}.keys()
min(keys)
```

### Disclaimer

Since AST parsing does not always tell us the type of an object, there may be
false positives and undesirable rewrites or bugs. With that said the tool is
designed to err on the side of not rewriting rather than being very clever and
rewriting as much as possible. To exclude rewrite, see the above section. PRs
are always welcome to help out!

## Features

### `builtins`

Rewrites builtin calls that have iterable arguments

```diff
 # simple cases
-min({1: 2, 3: 4}.keys())
+min({1: 2, 3: 4})

-min(d.keys())
+min(d)

-min(f().keys())
+min(f())

 # more complex cases
-min(d1().x.y(1, 2 ,3, (4, 5)).keys())
+min(d1().x.y(1, 2, 3, (4, 5)))
```

### `zip`

Rewrites relevant arguments in `zip()`

```diff
-zip(d.keys(), {}.keys(), f().keys(), [1, 2, 3])
+zip(d, {}, f(), [1, 2, 3])
```

### `map` / `filter`

Rewrites relevant arguments in `map` and `filter`

```diff
-map(lambda x: x*2, d.keys())
+map(lambda x: x*2, d)

-filter(None, d.keys())
+filteR(None, d)
```

### `in`

Rewrites relevant comparisons using `in`

```diff
-if x in d.keys():
+if x in d:
     pass
```

### comprehensions

Rewrites relevant list/dict/set comprehensions and generator expressions

```diff
-[x for x in d.keys()]
+[x for x in d]

-(x for x in d.keys())
+(x for x in d)

-{x for x in d.keys()}
+{x for x in d}

-{x: x for x in d.keys()}
+{x: x for x in d}
```

For additional linting in this space check out [`flake8-comprehensions`][flake8-comprehensions].

### iteration

Rewrites iteration

```diff
-for _ in d.keys(): pass
+for _ in d: pass

-for _ in {}.keys(): pass
+for _ in {}: pass

-for _ in f().keys(): pass
+for _ in f(): pass
```

## Acknowledgements

This tool would not be possible without guidance and tools from [Anthony
Sottile][asottile], specifically, [`pyupgrade`][pyupgrade] and
[`pre-commit`][pre-commit]. `unkey` is heavily adapted from the former and code
is attributed wherever possible. Thank you!

[asottile]: https://github.com/asottile
[flake8-comprehensions]: https://pypi.org/project/flake8-comprehensions/
[pre-commit]: https://pre-commit.com
[pyupgrade]: https://pypi.org/project/pyupgrade/
