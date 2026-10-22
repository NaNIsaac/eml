# EML against the paper

Source: A. Odrzywołek, "All elementary functions from a single binary operator", arXiv:2603.21852 (v1 2026-03-23, v2 2026-04-04). Section and table numbers below are from the v2 HTML text. Not read: the Supplementary Information, the author's EML compiler (github.com/VA00/SymbolicRegressionPackage, `EML_toolkit/`), and the Zenodo record 10.5281/zenodo.19183008. Follow-up: T. Stachowiak, "Algebraic structure behind Odrzywołek's EML operator", arXiv:2604.23893.

This repo started on 2026-04-15, three weeks after v1.

## What the paper claims and what this repo does

| | Paper | This repo |
|---|---|---|
| Operator | `eml(x, y) = exp(x) − ln(y)`, Eq. (3) | `e(x, y)`, same definition |
| Terminals | grammar `S → 1 \| eml(S, S)`, plus input variables (Sect. 4.2) | literal `1` plus numeric arguments. Every stdlib macro expands to `e` and number literals only (tested). The REPL also accepts `+ - * / **` between numbers, so input is not restricted to the grammar. |
| Number model | complex, principal branch (Sect. 1); some compiled formulas rely on `ln 0 = −∞`, `e^{−∞} = 0` (Sect. 4.1); "pure Python" is said not to work out of the box | `cmath`: principal branch, `ln(0)` raises, no infinities. Constructions that pass through `ln 0` cannot be used here. |
| `ln` | Eq. (5): `ln z = eml(1, eml(eml(1, z), 1))`, K = 7 | `ln(x) = e(zero(), e(e(zero(), x), 1))`: the same construction with 0 in place of the two outer 1s, K = 19. Eq. (5) typed into the REPL gives identical values at 2, −2, −1, i, −2−0i, 0.5. |
| Negative real axis | Sect. 4.1: with the principal branch, Eq. (5) gives the wrong sign there (`ln(−1) = −iπ`) | True in exact arithmetic for both forms. In double precision `fl(π) < π`, so the intermediate `Im = −fl(π)` stays inside the strip and both forms return `cmath.log(x)`, including the `−0.0` side of the cut (tested). Any derivation of `i` or `π` through `ln(−1)` depends on this rounding. |

## Sizes

K is the RPN length (leaves plus `e` nodes), the paper's measure. Paper values are Table 4, "compiler / direct search".

| | this repo | paper |
|---|---|---|
| 0 | 7 | 7 / 7 |
| exp x | 3 | 3 / 3 |
| ln x | 19 | 7 / 7 |
| x − y | 23 | 83 / 11 |
| −x | 33 | 57 / 15 |
| x + y | 55 | 27 / 19 |
| x · y | 93 | 41 / 17 |

`sub(a, b) = e(ln a, exp b)` with the paper's Eq. (5) for `ln` has K = 1 + 7 + 3 = 11, the paper's direct-search size for x − y. The gap in the other rows comes mostly from `ln` (K 19 instead of 7) and from building `add` and `mul` on `neg`.

## Implemented and not implemented

Implemented in `stdlib.eml`: 0, 1, exp, ln, 1 − ln x, 1 − x, x − y, −x, x + y, x · y, identity. `e` itself is `e(1, 1)` and needs no macro.

Not implemented, though the paper states they are reachable: the constants −1, 2, 1/2, i, π, √2; 1/x, x/y, x^y, √x, x², log_x y; trigonometric, hyperbolic and inverse functions. The paper gives no explicit trees for trigonometric functions in the text ("too large to be shown in print", Sect. 4.2).

## Domains (each one tested in `tests/test_engine.py`)

`ln(exp(w)) = w` only for −π < Im w ≤ π. Every derivation that sends a value through `exp` and back through `ln` inherits that strip. Outside it the result is off by a whole multiple of 2πi.

| macro | fails at | strip | overflow (`exp` above Re ≈ 709.78) |
|---|---|---|---|
| `one_minus_ln(x)`, `ln(x)` | x = 0 | none | none |
| `sub1(x)` | none | −π < Im x ≤ π | Re x < 709.78 |
| `sub(a, b)` | a = 0 | −π < Im b ≤ π | Re b < 709.78 |
| `neg(x)` | x = 1 | −π < Im x < π | Re x < 709.78 |
| `add(a, b)` | a = 0, b = 1 | −π < Im b < π | \|Re b\| < 709.78 |
| `mul(a, b)` | a ∈ {0, 1}, b ∈ {0, e} | none: the outer `exp` removes the 2πi errors | only when the product itself overflows |

Inside these domains the relative error against direct `cmath` arithmetic stayed below 1e-14 on a 12-point real and complex grid. Near the excluded points (b = 1 + 1e-12 in `add`, a = 1 + 1e-9 in `mul`) the error stayed at rounding level.

## Limits of the implementation

- Expansion is textual and repeats a regex search over the whole string, so its cost grows with the square of the expansion length. It stops after 1000 macro substitutions and reports "possible recursion"; 29 nested `mul` calls hit that cap even though nothing recurses.
- Evaluation used Python's `eval` until #2. That capped the depth at 200 nested parentheses (ten nested `mul`). The parser that replaced it has no depth limit.
- A macro that uses its argument twice (`sq(x) = mul(x, x)`) doubles its argument's text, so repeated squaring grows exponentially.

## Minimum completion (proposal; Isaac decides)

1. The stdlib reaches the constants and operations the paper lists as the scientific-calculator set: at least −1, 2, i, π, 1/x, x/y, x^y, √x and one trigonometric function, each with a domain comment.
2. Each stdlib macro has an identity test on a real and complex grid and a test for each excluded point, as the current ones do.
3. Each macro's K is recorded next to the paper's Table 4 value.

## Open tasks

- Derive the missing operations above. `i` and `π` need `ln(−1)`; see the negative-axis row.
- Decide whether `ln` should switch to Eq. (5) (K 7 instead of 19). It changes every derived size, not the values.
- Decide on a strict mode that accepts only `e`, `1` and inputs, so that typed expressions are guaranteed to be pure EML.
- Decide whether to emulate `ln 0 = −∞` and `e^{−∞} = 0`, which would admit the paper's extended-real constructions.
- Expand macros on a tree instead of on text, which removes the 1000-step cap and the quadratic cost.
- Compare the stdlib against the author's compiler output and the Supplementary Information, which were not read for this note.
