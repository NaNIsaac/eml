import cmath
import re

class EMLEngine:
    def __init__(self):
        self.macros = {
            "ZERO": {"params": [], "expr": "e(1, e(e(1, 1), 1))"}
        }

    def define(self, line):
        match = re.match(r"DEF\s+(\w+)\((.*)\)\s*=\s*(.*)", line)
        if match:
            name, params, expr = match.groups()
            self.macros[name] = {
                "params": [p.strip() for p in params.split(",") if p.strip()],
                "expr": expr.strip()
            }
            return name
        return None
    
    # def load_stdlib(self, filepath):
    #     """.eml 파일을 읽어 매크로를 등록함"""
    #     if not os.path.exists(filepath):
    #         return
            
    #     with open(filepath, "r", encoding="utf-8") as f:
    #         for line in f:
    #             line = line.strip()
    #             # 빈 줄이나 주석(#) 무시
    #             if not line or line.startswith("#"):
    #                 continue
                
    #             if line.startswith("DEF"):
    #                 self.define(line)
    
    def _expand(self, expr):
        while True:
            found = False
            for name in self.macros:
                idx = expr.find(name + "(")
                if idx != -1:
                    found = True
                    start = idx + len(name)
                    end = self._find_matching_paren(expr, start)
                    if end == -1: break
                    arg_str = expr[start+1:end]
                    args = self._split_args(arg_str)
                    body = self.macros[name]["expr"]
                    for p, a in zip(self.macros[name]["params"], args):
                        body = re.sub(rf"\b{p}\b", f"({a})", body)
                    expr = expr[:idx] + body + expr[end+1:]
                    break
            if not found: break
        return expr

    def _find_matching_paren(self, s, start):
        count = 0
        for i in range(start, len(s)):
            if s[i] == '(': count += 1
            elif s[i] == ')':
                count -= 1
                if count == 0: return i
        return -1

    def _split_args(self, s):
        args, curr, depth = [], [], 0
        for char in s:
            if char == ',' and depth == 0:
                args.append("".join(curr).strip()); curr = []
            else:
                if char == '(': depth += 1
                elif char == ')': depth -= 1
                curr.append(char)
        args.append("".join(curr).strip())
        return args

    def eval_expr(self, expr):
        raw = self._expand(expr)
        def e(x, y): return cmath.exp(x) - cmath.log(y)
        final_code = raw.replace("0", "0.0").replace("1", "1.0")
        try:
            res = eval(final_code, {"__builtins__": None}, {"e": e, "cmath": cmath})
            return res, raw
        except Exception as err:
            raise Exception(f"Calculation Error: {err}")