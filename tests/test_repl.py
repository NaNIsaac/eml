from eml.repl import start_repl


def run(monkeypatch, capsys, lines):
    feed = iter(lines)
    monkeypatch.setattr("builtins.input", lambda _prompt: next(feed))
    start_repl()
    return capsys.readouterr().out


def test_define_and_evaluate(monkeypatch, capsys):
    out = run(monkeypatch, capsys, ["DEF sq(x) = mul(x, x)", "sq(3)", "exit"])
    assert "Defined: sq" in out
    assert "[RESULT]   9.00000000" in out


def test_macro_name_starting_with_def(monkeypatch, capsys):
    out = run(monkeypatch, capsys, ["DEF deff(x) = x", "deff(2)", "quit"])
    assert "[RESULT]   2.00000000" in out
    assert "invalid DEF" not in out


def test_errors_are_reported_not_raised(monkeypatch, capsys):
    out = run(monkeypatch, capsys, ["ln(0)", "DEF", "exit"])
    assert out.count("[ERROR]") == 2
