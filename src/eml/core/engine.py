import cmath
import operator
import re


class EMLEngine:
    MAX_EXPAND_ITERS = 1000

    def __init__(self):
        self.macros: dict[str, dict] = {"ZERO": {"params": [], "expr": "e(1, e(e(1, 1), 1))"}}

    def define(self, line):
        match = re.match(r"(?i)DEF\s+(\w+)\s*\((.*)\)\s*=\s*(.*)", line)
        if not match:
            return None
        name, params, expr = match.groups()
        if name == "e":
            raise ValueError("cannot redefine base operator 'e'")
        params = [p.strip() for p in params.split(",") if p.strip()]
        if "e" in params:
            raise ValueError("'e' cannot be a parameter name; it is the base operator")
        self.macros[name] = {"params": params, "expr": expr.strip()}
        return name

    def load_stdlib(self, filepath):
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if re.match(r"(?i)DEF\b", line):
                    self.define(line)

    def _expand(self, expr):
        # Longest name first so that e.g. `exp(` isn't shadowed by a future `ex` macro.
        for _ in range(self.MAX_EXPAND_ITERS):
            replaced = False
            for name in sorted(self.macros, key=len, reverse=True):
                m = re.search(rf"\b{re.escape(name)}\s*\(", expr)
                if not m:
                    continue
                paren = expr.index("(", m.end() - 1)
                end = self._find_matching_paren(expr, paren)
                if end == -1:
                    raise ValueError(f"unmatched parenthesis in call to '{name}'")
                arg_str = expr[paren + 1 : end]
                args = self._split_args(arg_str) if arg_str.strip() else []
                macro = self.macros[name]
                if len(args) != len(macro["params"]):
                    raise ValueError(
                        f"{name} expects {len(macro['params'])} arg(s), got {len(args)}"
                    )
                body = self._substitute_params(macro["expr"], macro["params"], args)
                expr = expr[: m.start()] + body + expr[end + 1 :]
                replaced = True
                break
            if not replaced:
                return expr
        raise RuntimeError(
            f"macro expansion exceeded {self.MAX_EXPAND_ITERS} iterations (possible recursion)"
        )

    @staticmethod
    def _substitute_params(body, params, args):
        # Two-pass with sentinel tokens so param names can't collide with
        # macro names or with each other's replacement text.
        tokens = [f"\x00P{i}\x00" for i in range(len(params))]
        for p, tok in zip(params, tokens, strict=True):
            body = re.sub(rf"\b{re.escape(p)}\b", tok, body)
        for tok, a in zip(tokens, args, strict=False):
            body = body.replace(tok, f"({a})")
        return body

    @staticmethod
    def _find_matching_paren(s, start):
        count = 0
        for i in range(start, len(s)):
            if s[i] == "(":
                count += 1
            elif s[i] == ")":
                count -= 1
                if count == 0:
                    return i
        return -1

    @staticmethod
    def _split_args(s):
        args, curr, depth = [], [], 0
        for char in s:
            if char == "," and depth == 0:
                args.append("".join(curr).strip())
                curr = []
            else:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                curr.append(char)
        args.append("".join(curr).strip())
        return args

    def eval_expr(self, expr):
        raw = self._expand(expr)
        try:
            return _evaluate(_to_rpn(raw)), raw
        except Exception as err:
            raise RuntimeError(f"Calculation Error: {err}") from err


# The expansion is evaluated without Python's eval: the parser rejects more than
# 200 nested parentheses, which a few nested `mul` calls already exceed.
_TOKEN = re.compile(
    r"\s*(?:(?P<num>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?j?)|(?P<name>\w+)|(?P<op>\*\*|[-+*/(),]))"
)
_BINARY = {
    "+": (1, operator.add),
    "-": (1, operator.sub),
    "*": (2, operator.mul),
    "/": (2, operator.truediv),
    "**": (4, operator.pow),
}
_UNARY = {"u+": operator.pos, "u-": operator.neg}
_UNARY_PREC = 3  # between * and **, as in Python: -2**2 == -4, 2**-1 == 0.5


def _precedence(op):
    return _UNARY_PREC if op in _UNARY else _BINARY[op][0]


def _tokens(s):
    pos = 0
    while pos < len(s.rstrip()):
        m = _TOKEN.match(s, pos)
        if not m:
            raise ValueError(f"unexpected character {s[pos:].lstrip()[0]!r}")
        pos = m.end()
        kind = m.lastgroup
        yield kind, m.group(kind)


def _number(tok):
    # Integer literals become floats, as Python literals with a trailing ".0" would.
    return complex(0, float(tok[:-1])) if tok.endswith("j") else float(tok)


def _to_rpn(s):
    """Shunting-yard over numbers, + - * / **, unary +/-, parentheses and e(x, y)."""
    out, ops, groups = [], [], []  # groups: [is_call, comma count] per open parenthesis
    prev = None  # "value", "op", "e", "(" or ","
    for kind, tok in _tokens(s):
        if prev == "e" and tok != "(":
            raise ValueError("'e' must be called as e(x, y)")
        if kind in ("num", "name"):
            if prev == "value":
                raise ValueError(f"unexpected {tok!r}")
            if kind == "num":
                out.append(_number(tok))
                prev = "value"
            elif tok == "e":
                ops.append("e")
                prev = "e"
            else:
                raise ValueError(f"unknown name {tok!r}")
        elif tok == "(":
            if prev == "value":
                raise ValueError("unexpected '('")
            groups.append([prev == "e", 0])
            ops.append("(")
            prev = "("
        elif tok in ",)":
            if prev in (None, "op", "(", ","):
                raise ValueError(f"unexpected {tok!r}")
            while ops and ops[-1] != "(":
                out.append(ops.pop())
            if not ops:
                raise ValueError(f"unmatched {tok!r}")
            if tok == ",":
                if not groups[-1][0]:
                    raise ValueError("unexpected ','")
                groups[-1][1] += 1
                prev = ","
                continue
            ops.pop()
            is_call, commas = groups.pop()
            if is_call:
                if commas != 1:
                    raise ValueError(f"e expects 2 args, got {commas + 1}")
                out.append(ops.pop())
            prev = "value"
        elif prev in (None, "op", "(", ","):
            if tok not in "+-":
                raise ValueError(f"unexpected {tok!r}")
            ops.append("u" + tok)
            prev = "op"
        else:
            prec = _BINARY[tok][0]
            while ops and ops[-1] not in ("(", "e"):
                top = _precedence(ops[-1])
                if top > prec or (top == prec and tok != "**"):
                    out.append(ops.pop())
                else:
                    break
            ops.append(tok)
            prev = "op"
    if prev != "value":
        raise ValueError("incomplete expression")
    while ops:
        if ops[-1] == "(":
            raise ValueError("unmatched '('")
        out.append(ops.pop())
    return out


def _evaluate(rpn):
    stack = []
    for item in rpn:
        if not isinstance(item, str):
            stack.append(item)
        elif item == "e":
            y = stack.pop()
            stack.append(cmath.exp(stack.pop()) - cmath.log(y))
        elif item in _UNARY:
            stack.append(_UNARY[item](stack.pop()))
        else:
            b = stack.pop()
            stack.append(_BINARY[item][1](stack.pop(), b))
    return stack.pop()
