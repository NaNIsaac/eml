import cmath
import itertools
import math
import re
from pathlib import Path

import pytest

from eml.core.engine import EMLEngine

STDLIB = Path(__file__).parents[1] / "src" / "eml" / "stdlib.eml"

# Inside the documented domains: no 0 or 1 where excluded, |Im| < pi, |Re| well below 709.
POINTS = [0.3, 2.0, -2.0, 7.5, -0.4, 1e-3, 50.0, -50.0, 1.5 + 2j, -2 - 1j, 0.5j, 0.1 - 3j]


@pytest.fixture
def engine():
    eng = EMLEngine()
    eng.load_stdlib(STDLIB)
    return eng


def value(engine, expr):
    return engine.eval_expr(expr)[0]


def close(a, b):
    return cmath.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def test_zero_and_e(engine):
    assert abs(value(engine, "zero()")) < 1e-15
    assert abs(value(engine, "ZERO()")) < 1e-15
    assert close(value(engine, "e(1, 1)"), math.e)


@pytest.mark.parametrize("x", POINTS)
def test_unary_identities(engine, x):
    assert close(value(engine, f"exp({x!r})"), cmath.exp(x))
    assert close(value(engine, f"ln({x!r})"), cmath.log(x))
    assert close(value(engine, f"one_minus_ln({x!r})"), 1 - cmath.log(x))
    assert close(value(engine, f"sub1({x!r})"), 1 - x)
    assert close(value(engine, f"neg({x!r})"), -x)
    assert close(value(engine, f"id({x!r})"), x)


@pytest.mark.parametrize(("a", "b"), list(itertools.product(POINTS, POINTS)))
def test_binary_identities(engine, a, b):
    assert close(value(engine, f"sub({a!r}, {b!r})"), a - b)
    assert close(value(engine, f"add({a!r}, {b!r})"), a + b)
    assert close(value(engine, f"mul({a!r}, {b!r})"), a * b)


def test_readme_example(engine):
    engine.define("DEF sq(x) = mul(x, x)")
    assert close(value(engine, "sq(3)"), 9)


@pytest.mark.parametrize(
    "name", ["zero", "exp", "ln", "one_minus_ln", "sub1", "sub", "neg", "add", "mul"]
)
def test_stdlib_expands_to_the_single_operator(engine, name):
    args = ", ".join(["2"] * len(engine.macros[name]["params"]))
    raw = engine.eval_expr(f"{name}({args})")[1]
    assert set(re.sub(r"\d+(\.\d*)?|\s", "", raw)) <= set("e(),")


@pytest.mark.parametrize(
    "expr",
    [
        "ln(0)",
        "one_minus_ln(0)",
        "sub(0, 3)",
        "neg(1)",
        "add(0, 3)",
        "add(2, 1)",
        "mul(0, 3)",
        "mul(1, 3)",
        "mul(3, 0)",
        f"mul(3, {math.e!r})",
    ],
)
def test_documented_singular_points_raise(engine, expr):
    with pytest.raises(RuntimeError, match="Calculation Error"):
        engine.eval_expr(expr)


@pytest.mark.parametrize(
    ("expr", "exact", "turns"),
    [("sub(5, 4j)", 5 - 4j, 1), ("sub(5, -4j)", 5 + 4j, -1), ("neg(3.5j)", -3.5j, 1)],
)
def test_outside_the_strip_off_by_2_pi_i(engine, expr, exact, turns):
    # ln(exp(w)) folds Im w back into (-pi, pi]; the result is off by a whole turn.
    assert close(value(engine, expr), exact + 2j * math.pi * turns)


def test_mul_is_exact_off_the_strip(engine):
    # The outer exp of mul hides the 2*pi*i errors of add.
    assert close(value(engine, "mul(-2, -3)"), 6)
    assert close(value(engine, "mul(1+2j, 3-1j)"), (1 + 2j) * (3 - 1j))


@pytest.mark.parametrize("x", [-1, -2, complex(-2, -0.0), 1j, -1j])
def test_ln_follows_cmath_on_the_branch_cut(engine, x):
    # Exactly, ln(x) on the negative axis would flip to ln|x| - i*pi; fl(pi) < pi prevents it.
    assert close(value(engine, f"ln({x!r})"), cmath.log(x))


@pytest.mark.parametrize(
    ("expr", "ok"), [("sub(2, 709.0)", True), ("sub(2, 710.0)", False), ("add(2, -710.0)", False)]
)
def test_exp_overflow_bound(engine, expr, ok):
    if ok:
        value(engine, expr)
    else:
        with pytest.raises(RuntimeError, match="range"):
            engine.eval_expr(expr)


def test_deep_nesting_beyond_python_parser_limit(engine):
    expr = "2"
    for _ in range(20):
        expr = f"mul({expr}, 2)"
    value_, raw = engine.eval_expr(expr)
    assert raw.count("(") > 200
    assert cmath.isclose(value_, 2**21, rel_tol=1e-10)


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("1e-5", 1e-5),
        ("ln(1e-300)", cmath.log(1e-300)),
        ("2.5e-3j", 2.5e-3j),
        (".5", 0.5),
        ("1 + 2j", 1 + 2j),
        ("-2**2", -4),
        ("2**-1", 0.5),
        ("2**3**2", 512),
        ("2*3 - 8/4", 4),
        ("-(1 - 3)", 2),
    ],
)
def test_numeric_literals_and_arithmetic(engine, expr, expected):
    assert close(value(engine, expr), expected)


@pytest.mark.parametrize(
    "expr", ["().__class__", "abs(2)", "x", "e(1)", "e(1, 2, 3)", "(1, 2)", "2 3", "e(1, 1", "2 +"]
)
def test_rejects_anything_but_arithmetic_and_e(engine, expr):
    with pytest.raises(RuntimeError, match="Calculation Error"):
        engine.eval_expr(expr)


def test_define():
    eng = EMLEngine()
    assert eng.define("DEF f(x, y) = e(y, x)") == "f"
    assert eng.define("def g() = 1") == "g"
    assert eng.define("DEF broken") is None
    with pytest.raises(ValueError, match="base operator"):
        eng.define("DEF e(x) = x")
    with pytest.raises(ValueError, match="parameter"):
        eng.define("DEF h(e) = e(e, 1)")


def test_parameters_do_not_capture_each_other():
    eng = EMLEngine()
    eng.define("DEF swap(x, y) = e(y, x)")
    eng.define("DEF exp(x) = e(x, 1)")
    # A parameter shadows a macro of the same name inside the body.
    eng.define("DEF shadow(exp) = e(exp, 1)")
    assert close(value(eng, "swap(1, 2)"), cmath.exp(2))
    assert close(value(eng, "shadow(exp(1))"), cmath.exp(math.e))


def test_argument_count_and_recursion(engine):
    with pytest.raises(ValueError, match="expects 2"):
        engine.eval_expr("sub(1)")
    engine.define("DEF loop(x) = loop(x)")
    with pytest.raises(RuntimeError, match="recursion"):
        engine.eval_expr("loop(1)")
