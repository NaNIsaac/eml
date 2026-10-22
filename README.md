# eml

A small REPL that builds arithmetic from a single binary operator, `e(x, y) = exp(x) - ln(y)` (EML, "exp minus log"), by textual macro expansion and evaluates the result with complex `cmath`.

An independent mathematical exploration, started after A. Odrzywołek, "All elementary functions from a single binary operator" ([arXiv:2603.21852](https://arxiv.org/abs/2603.21852)). Unfinished: [docs/paper.md](docs/paper.md) compares the code with the paper and lists what is implemented, the verified domains, and the open tasks. Not related to the X-ray analysis repos.

## Requirements

Python 3.14+ (no third-party dependencies).

## Usage

```bash
uv run eml            # or: python -m eml  (with src/ on the path)
```

```
>> DEF sq(x) = mul(x, x)
Defined: sq
>> sq(3)
  [EXPANDED] e((e(e(e(1, e(e(1, 1), 1)), ...
  [RESULT]   9.00000000 + -0.00000000j
>> exit
```

Input is either `DEF name(args) = expr` or an expression; `exit` or `quit` leaves. Every macro is expanded down to nested `e(...)` calls, the expansion is printed, then evaluated. Expressions may also contain numbers (`2`, `1e-5`, `1+2j`), `+ - * / **` and parentheses. `src/eml/stdlib.eml` is loaded at start and defines `zero`, `one`, `exp`, `id`, `one_minus_ln`, `sub1`, `ln`, `sub`, `neg`, `add`, `mul`; the comments there list the domain restrictions of each derivation (e.g. `add(a, b)` needs a != 0, b != 1, and -pi < Im b < pi).

## Tests

```bash
uv run --with pytest pytest -q
```

## Structure

```
src/eml/repl.py         REPL loop
src/eml/core/engine.py  EMLEngine: DEF parsing, macro expansion, evaluation
src/eml/stdlib.eml      derived functions
docs/paper.md           comparison with the paper, domains, open tasks
```
