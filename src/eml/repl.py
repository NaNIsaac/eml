from pathlib import Path
from .core.engine import EMLEngine


def start_repl():
    engine = EMLEngine()

    stdlib_path = Path(__file__).parent / "stdlib.eml"
    if stdlib_path.exists():
        try:
            engine.load_stdlib(stdlib_path)
            print(f"Standard library loaded from {stdlib_path}")
        except Exception as e:
            print(f"Failed to load stdlib: {e}")

    print("EML Interpreter v1.0.0")
    print("Base Operator: e(x, y) = exp(x) - ln(y)")
    print("Commands: DEF <name>(<args>) = <expr> | <expression> | exit\n")

    while True:
        try:
            line = input(">> ").strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print("\nTerminated.")
            break

        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break

        try:
            if line[:3].upper() == "DEF":
                name = engine.define(line)
                if name:
                    print(f"Defined: {name}")
                else:
                    print("  [ERROR] invalid DEF syntax")
            else:
                res, raw = engine.eval_expr(line)
                print(f"  [EXPANDED] {raw}")
                print(f"  [RESULT]   {res.real:.8f} + {res.imag:.8f}j")
        except Exception as e:
            print(f"  [ERROR] {e}")


if __name__ == "__main__":
    start_repl()
