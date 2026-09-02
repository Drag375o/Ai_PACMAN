# Why does run() exit after one move?

from maze import parse_maze
from pathfinding import distance_map
from ai import choose_target
import ai

pellets, pac_start, ghost_starts = parse_maze()
pellets = set(pellets)
gd = [distance_map(c) for c in ghost_starts]

print(f"pac_start={pac_start}  ghosts={ghost_starts}")
print(f"REVERSAL_PENALTY={ai.REVERSAL_PENALTY}  PANIC_COST={ai.PANIC_COST}")
print(f"pellets={len(pellets)}\n")

cell = pac_start
last = None
target = None

for step in range(8):
    target, path = choose_target(cell, pellets, gd, target, last)
    print(f"step {step}: from {cell} last={last}")
    print(f"   target={target}  path={path}")

    if not path:
        print("   -> EMPTY PATH, run() would break here")
        break

    tail = path[1:]
    if not tail:
        print("   -> path has no tail after dropping first cell, break")
        break

    last = cell
    
    cell = tail[0]
    if cell in pellets:
        pellets.remove(cell)
    print(f"   moved to {cell}, pellets left {len(pellets)}")