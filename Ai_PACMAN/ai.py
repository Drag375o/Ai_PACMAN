# Pac-Man's decision-making. This is where "the AI" lives.
#
# pathfinding.py answers "how do I get to X, and what does it cost?"
# This file answers "which X should I want?"

from maze import manhattan, neighbors
from pathfinding import find_path_costed

# How many nearest pellets to run A* on. Must be wide enough that the
# shortlist holds genuinely different options, not one tight cluster.
# (Measured: at 12 the shortlist was one dense cluster and every candidate
# scored the same danger, so the penalty could not change the decision.)
CANDIDATE_COUNT = 24

# A ghost is considered threatening within this many steps.
DANGER_RADIUS = 6

# Extra cost of entering a cell, per unit of danger.
# Higher = more cowardly. This single number tunes the personality:
# 0 walks through ghosts, 30 flees before entering the danger zone at all.
DANGER_WEIGHT = 8

# If even the best pellet costs more than this, retreat instead.
PANIC_COST = 60


def cell_danger(cell, ghost_distances):
    # Danger of one cell: 0 when ghosts are far, rising as they get closer.
    # Uses BFS distances, so a wall between cell and ghost counts as safe.
    # Multiple ghosts SUM, so cells between two ghosts are worst of all -
    # and adding a second ghost needed no change to this function.
    total = 0
    for distances in ghost_distances:
        steps_away = distances.get(cell)
        if steps_away is None:
            continue                       # unreachable by this ghost
        if steps_away < DANGER_RADIUS:
            total += DANGER_RADIUS - steps_away
    return total


def make_cost_function(ghost_distances):
    # Build the extra step cost A* will use. None when there is no threat.
    if not ghost_distances:
        return None

    def cost(cell):
        return DANGER_WEIGHT * cell_danger(cell, ghost_distances)

    return cost


def choose_escape(pac_cell, ghost_distances):
    # No safe pellet available: step to whichever neighbouring cell is
    # furthest from the ghosts. Still a scored choice, not a hard-coded
    # "if ghost_left: move_right" rule.
    options = neighbors(*pac_cell)
    if not options:
        return None, []
    safest = max(options, key=lambda cell: min(
        (d.get(cell, 99) for d in ghost_distances), default=99
    ))
    return None, [pac_cell, safest]


def choose_target(pac_cell, pellets, ghost_distances=()):
    # Pick a pellet and return (target_cell, path_to_it).
    #
    #   1. Shortlist nearest pellets by Manhattan distance (cheap).
    #   2. Run danger-aware A* on those for risk-adjusted cost (accurate).
    #   3. Lowest cost wins.
    #
    # Nothing here says "avoid ghosts". Avoidance emerges from the cost.
    # Returns (None, None) if nothing reachable is left.
    if not pellets:
        return None, None

    cell_cost = make_cost_function(ghost_distances)

    candidates = sorted(pellets, key=lambda cell: manhattan(pac_cell, cell))
    candidates = [c for c in candidates if c != pac_cell][:CANDIDATE_COUNT]

    best_target = None
    best_path = None
    best_cost = float("inf")

    for pellet in candidates:
        path, cost = find_path_costed(pac_cell, pellet, cell_cost)
        if path is None:
            continue
        if cost < best_cost:
            best_cost = cost
            best_target = pellet
            best_path = path

    # Everything reachable is dangerous - retreat rather than walk into it.
    if ghost_distances and (best_path is None or best_cost > PANIC_COST):
        return choose_escape(pac_cell, ghost_distances)

    return best_target, best_path