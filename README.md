# eml

Moved into a private scratch repo; no longer maintained.

A small REPL that builds arithmetic from a single binary operator, `e(x, y) = exp(x) - ln(y)` (EML, "exp minus log"), by textual macro expansion and evaluates the result with complex `cmath`.

Toy project, not related to the X-ray analysis repos.

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

Input is either `DEF name(args) = expr` or an expression; `exit` or `quit` leaves. Every macro is expanded down to nested `e(...)` calls, the expansion is printed, then evaluated. `src/eml/stdlib.eml` is loaded at start and defines `zero`, `one`, `exp`, `id`, `one_minus_ln`, `sub1`, `ln`, `sub`, `neg`, `add`, `mul`; the comments there list the domain restrictions of each derivation (e.g. `add(a, b)` needs a != 0, b != 1).

## Structure

```
src/eml/repl.py         REPL loop
src/eml/core/engine.py  EMLEngine: DEF parsing, macro expansion, evaluation
src/eml/stdlib.eml      derived functions
```
