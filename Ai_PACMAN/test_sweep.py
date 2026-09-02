# Sweep REVERSAL_PENALTY. Verbose on the first seed so we can see any
# early exit rather than guessing at it.

import ai
from test_staleness import run

# Sanity check: does a single run behave at all?
print("Sanity run (penalty=4, seed=0):")
ai.REVERSAL_PENALTY = 4
result = run(True, 0)
labels = ["deaths", "toward", "left", "switches", "moves",
          "ate", "mid", "rev", "esc"]
for name, value in zip(labels, result):
    print(f"   {name:>9} = {value}")

print(f"\n{'penalty':>8} {'deaths':>7} {'left':>6} {'moves':>7} "
      f"{'mid':>5} {'rev':>5}")

for penalty in [0, 4, 8, 12, 16, 24, 32]:
    ai.REVERSAL_PENALTY = penalty
    totals = [0] * 9
    runs = 8
    for seed in range(runs):
        totals = [t + r for t, r in zip(totals, run(True, seed))]
    avg = [t / runs for t in totals]
    deaths, toward, left, switches, moves, ate, mid, rev, esc = avg
    print(f"{penalty:>8} {deaths:>7.1f} {left:>6.1f} {moves:>7.0f} "
          f"{mid:>5.0f} {rev:>5.0f}")