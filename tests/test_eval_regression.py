"""The parser that replaced eval (#2) must give the same values as eval did.

The reference below is the evaluation step of the engine before #2, run on the same
platform as the new one, so the comparison does not depend on how a given libm rounds.
"""

import cmath
import re
from pathlib import Path

import pytest

from eml.core.engine import EMLEngine, _evaluate, _to_rpn

STDLIB = Path(__file__).parents[1] / "src" / "eml" / "stdlib.eml"

ARGS = [
    "0", "1", "2", "-2", "0.5", "2.5", "3", "-1", "1j", "-1j",
    "1+2j", "3-1j", "-2-0j", "1e5", "1.5e2", "10j", "2.718281828459045",
]  # fmt: skip


def corpus():
    cases = ["zero()", "one()", "ZERO()", "e(1,1)", "e(0.5, 2)"]
    cases += ["2**3", "1+2", "-2**2", "2**-1", "1/4", "2*3-1"]
    for f in ["exp", "ln", "one_minus_ln", "sub1", "neg", "id", "sq"]:
        cases += [f"{f}({a})" for a in ARGS]
    for f in ["sub", "add", "mul"]:
        cases += [f"{f}({a}, {b})" for a in ARGS[:12] for b in ARGS[:12]]
    expr = "2"
    for _ in range(9):
        expr = f"mul({expr}, 2)"
        cases.append(expr)
    return cases


def eval_before_2(raw):
    code = re.sub(r"(?<![\w.])\d+(?![\w.])", lambda m: m.group(0) + ".0", raw)

    def e(x, y):
        return cmath.exp(x) - cmath.log(y)

    return eval(code, {"__builtins__": {}}, {"e": e})


@pytest.fixture(scope="module")
def expansions():
    eng = EMLEngine()
    eng.load_stdlib(STDLIB)
    eng.define("DEF sq(x) = mul(x, x)")
    out = []
    for case in corpus():
        try:
            out.append((case, eng._expand(case)))
        except ValueError:
            out.append((case, None))
    return out


def test_corpus_size():
    assert len(corpus()) == 571


def test_same_repr_wherever_eval_succeeded(expansions):
    compared = 0
    for case, raw in expansions:
        if raw is None:
            continue
        try:
            old = eval_before_2(raw)
        except ValueError, OverflowError, SyntaxError:  # failed before #2 as well
            continue
        assert repr(_evaluate(_to_rpn(raw))) == repr(old), case
        compared += 1
    assert compared == 493
