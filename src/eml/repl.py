import os
import sys
from .core.engine import EMLEngine

def start_repl():
    engine = EMLEngine()

    stdlib_path = "stdlib.eml"
    # if os.path.exists(stdlib_path):
    #     try:
    #         # engine.py에 정의할 load_stdlib 호출
    #         engine.load_stdlib(stdlib_path)
    #         print(f"Standard library loaded from {stdlib_path}")
    #     except Exception as e:
    #         print(f"Failed to load stdlib: {e}")
    print("EML Interpreter v1.0.0")
    print("Base Operator: eml(x, y) = e^x - ln(y)")
    print("Commands: DEF <name>(<args>) = <expr> | <expression> | exit\n")

    while True:
        try:
            line = input(">> ").strip()
            if not line: 
                continue
            if line.lower() in ('exit', 'quit'): 
                break

            if line.startswith("DEF"):
                name = engine.define(line)
                if name:
                    print(f"Defined: {name}")
            else:
                res, raw = engine.eval_expr(line)
                print(f"  [EXPANDED] Length: {len(raw)} chars")
                print(f"  [RESULT]   {res.real:.8f} + {res.imag:.8f}j")

        except KeyboardInterrupt:
            print("\nTerminated.")
            break
        except Exception as e:
            print(f"  [ERROR] {e}")

if __name__ == "__main__":
    start_repl()