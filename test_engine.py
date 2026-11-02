import engine

assert engine.version_for("a@b.com") == engine.version_for("A@B.com")
assert engine.p_value(10, 100, 10, 100) == 1.0
assert engine.p_value(20, 100, 5, 100) < 0.01
row = lambda v, rep: {"version": v, "segment": "", "replied": rep}
assert engine.verdict(engine.tally([row("A", "0")] * 5 + [row("C", "1")] * 5, "version")).startswith("too early")
big = [row("A", "1")] * 10 + [row("A", "0")] * 20 + [row("C", "1")] * 1 + [row("C", "0")] * 29
assert engine.verdict(engine.tally(big, "version")).startswith("A wins")
close = [row("A", "1")] * 6 + [row("A", "0")] * 24 + [row("C", "1")] * 2 + [row("C", "0")] * 28
assert "could be luck" in engine.verdict(engine.tally(close, "version"))
print("ok")
