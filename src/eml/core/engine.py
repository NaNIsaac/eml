import cmath
import re


class EMLEngine:
    MAX_EXPAND_ITERS = 1000

    def __init__(self):
        self.macros: dict[str, dict] = {
            "ZERO": {"params": [], "expr": "e(1, e(e(1, 1), 1))"}
        }

    def define(self, line):
        match = re.match(r"(?i)DEF\s+(\w+)\s*\((.*)\)\s*=\s*(.*)", line)
        if not match:
            return None
        name, params, expr = match.groups()
        if name == "e":
            raise ValueError("cannot redefine base operator 'e'")
        self.macros[name] = {
            "params": [p.strip() for p in params.split(",") if p.strip()],
            "expr": expr.strip(),
        }
        return name

    def load_stdlib(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
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
                arg_str = expr[paren + 1:end]
                args = self._split_args(arg_str) if arg_str.strip() else []
                macro = self.macros[name]
                if len(args) != len(macro["params"]):
                    raise ValueError(
                        f"{name} expects {len(macro['params'])} arg(s), got {len(args)}"
                    )
                body = self._substitute_params(macro["expr"], macro["params"], args)
                expr = expr[:m.start()] + body + expr[end + 1:]
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
        for p, tok in zip(params, tokens):
            body = re.sub(rf"\b{re.escape(p)}\b", tok, body)
        for tok, a in zip(tokens, args):
            body = body.replace(tok, f"({a})")
        return body

    @staticmethod
    def _find_matching_paren(s, start):
        count = 0
        for i in range(start, len(s)):
            if s[i] == '(':
                count += 1
            elif s[i] == ')':
                count -= 1
                if count == 0:
                    return i
        return -1

    @staticmethod
    def _split_args(s):
        args, curr, depth = [], [], 0
        for char in s:
            if char == ',' and depth == 0:
                args.append("".join(curr).strip())
                curr = []
            else:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                curr.append(char)
        args.append("".join(curr).strip())
        return args

    def eval_expr(self, expr):
        raw = self._expand(expr)
        # Promote bare integer literals to floats; leave identifiers and
        # existing floats/scientific literals (e.g. 1e5, 3.14) alone.
        final_code = re.sub(r"(?<![\w.])\d+(?![\w.])", lambda m: m.group(0) + ".0", raw)

        def e(x, y):
            return cmath.exp(x) - cmath.log(y)

        try:
            res = eval(final_code, {"__builtins__": {}}, {"e": e})
            return res, raw
        except Exception as err:
            raise RuntimeError(f"Calculation Error: {err}") from err
