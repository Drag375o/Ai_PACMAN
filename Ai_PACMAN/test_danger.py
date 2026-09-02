# Diagnose the danger-aware A* without opening a window.

from maze import parse_maze, manhattan
from pathfinding import find_path, find_path_costed, distance_map
from ai import CANDIDATE_COUNT, DANGER_RADIUS, DANGER_WEIGHT, make_cost_function, cell_danger

pellets, pacman_start, ghost_starts = parse_maze()

pac_cell = (7, 5)
ghost_cell = (7, 9)
ghost_distances = [distance_map(ghost_cell)]
cell_cost = make_cost_function(ghost_distances)

print(f"Pac-Man at {pac_cell}, ghost at {ghost_cell}")
print(f"CANDIDATE_COUNT={CANDIDATE_COUNT}  DANGER_RADIUS={DANGER_RADIUS}  DANGER_WEIGHT={DANGER_WEIGHT}\n")

candidates = sorted(pellets, key=lambda c: manhattan(pac_cell, c))[:CANDIDATE_COUNT]

print(f"{'pellet':>10} {'steps':>6} {'danger':>7} {'cost':>7}")
rows = []
for pellet in candidates:
    plain = find_path(pac_cell, pellet)
    path, cost = find_path_costed(pac_cell, pellet, cell_cost)
    if path is None:
        continue
    steps = len(plain) - 1
    rows.append((cost, pellet, steps))
    print(f"{str(pellet):>10} {steps:>6} {cell_danger(pellet, ghost_distances):>7} {cost:>7}")

rows.sort()
print(f"\nDistinct costs: {len(set(c for c, _, _ in rows))} of {len(rows)} candidates")
print(f"CHOSEN: pellet {rows[0][1]}, {rows[0][2]} steps away, cost {rows[0][0]}")
print(f"Ghost is at {ghost_cell} - chosen pellet should be AWAY from it (col < 5)")

print("\n--- Does the route avoid the ghost? ---")
far_pellet = (7, 13)   # on the far side of the ghost
plain = find_path(pac_cell, far_pellet)
safe, cost = find_path_costed(pac_cell, far_pellet, cell_cost)
print(f"Plain A* to {far_pellet}: {len(plain) - 1} steps")
print(f"  closest approach to ghost: {min(ghost_distances[0].get(c, 99) for c in plain)}")
print(f"Danger-aware A* to {far_pellet}: {len(safe) - 1} steps, cost {cost}")
print(f"  closest approach to ghost: {min(ghost_distances[0].get(c, 99) for c in safe)}")