# Compares replanning strategies headlessly (no Pygame window).
#
# Lazy replan  : keep following the current A* path until it finishes, the
#                target is eaten, or a ghost steps next to our next cell.
# Replan always: recompute the target and path on every single move.
#
# Breaks down where moves are spent: legitimate target changes (target eaten)
# vs dithering (abandoned en route), physical reversals, and panic retreats.

import random
from maze import parse_maze, neighbors, manhattan
from pathfinding import distance_map
from ai import choose_target, DANGER_RADIUS

CHASE_RADIUS = 8


def step_ghost(ghost, pac_cell, rng):
    # Same greedy logic as update_ghost in main.py.
    options = neighbors(*ghost["cell"])
    if not options:
        return
    if manhattan(ghost["cell"], pac_cell) <= CHASE_RADIUS:
        target = min(options, key=lambda c: manhattan(c, pac_cell))
    else:
        back = (ghost["cell"][0] - ghost["dir"][0],
                ghost["cell"][1] - ghost["dir"][1])
        fwd = [c for c in options if c != back]
        target = rng.choice(fwd or options)
    ghost["dir"] = (target[0] - ghost["cell"][0], target[1] - ghost["cell"][1])
    ghost["cell"] = target


def run(always_replan, seed, max_moves=2000):
    rng = random.Random(seed)
    pellets, pac_start, ghost_starts = parse_maze()
    pac_cell = pac_start
    ghosts = [{"cell": c, "dir": (0, 0)} for c in ghost_starts]

    path = []
    target = None
    prev_target = None
    last_cell = None

    deaths = 0
    approach_steps = 0      # steps that reduced distance to an in-range ghost
    switches = 0            # how often the chosen target changed
    switch_after_eat = 0    # ...because we ate it (legitimate)
    switch_mid_path = 0     # ...while still en route (dithering)
    reversals = 0           # stepped back onto the cell we just left
    escape_steps = 0        # steps taken with no target (panic retreat)
    moves_used = 0
    tick = 0

    for move in range(max_moves):
        gd = [distance_map(g["cell"]) for g in ghosts]

        stale = not path or target not in pellets
        next_unsafe = bool(path) and any(d.get(path[0], 99) <= 1 for d in gd)

        if always_replan or stale or next_unsafe:
            old_target = target
            had_path = len(path) > 0
            target, new_path = choose_target(pac_cell, pellets, gd)
            path = new_path[1:] if new_path else []

            if target != prev_target:
                switches += 1
                if old_target is not None and old_target not in pellets:
                    switch_after_eat += 1
                elif had_path:
                    switch_mid_path += 1
                prev_target = target

            if target is None and path:
                escape_steps += 1

        if not path:
            break

        before = pac_cell
        pac_cell = path.pop(0)
        moves_used = move + 1

        if pac_cell == last_cell:
            reversals += 1
        last_cell = before

        for d in gd:
            if d.get(before, 99) < DANGER_RADIUS:
                if d.get(pac_cell, 99) < d.get(before, 99):
                    approach_steps += 1

        if pac_cell in pellets:
            pellets.remove(pac_cell)

        # Ghosts move on their own slower cadence (12 frames vs Pac-Man's 8).
        tick += 8
        while tick >= 12:
            tick -= 12
            for g in ghosts:
                step_ghost(g, pac_cell, rng)

        if any(g["cell"] == pac_cell for g in ghosts):
            deaths += 1
            pac_cell = pac_start
            for g, c in zip(ghosts, ghost_starts):
                g["cell"] = c
            path = []
            target = None
            prev_target = None
            last_cell = None
            if deaths >= 3:
                break

        if not pellets:
            break

    return (deaths, approach_steps, len(pellets), switches, moves_used,
            switch_after_eat, switch_mid_path, reversals, escape_steps)


if __name__ == "__main__":
    print(f"{'mode':>16} {'deaths':>7} {'left':>6} {'moves':>7} "
          f"{'sw':>5} {'ate':>5} {'mid':>5} {'rev':>5} {'esc':>5}")

    for label, flag in [("lazy replan", False), ("replan always", True)]:
        totals = [0] * 9
        runs = 8
        for seed in range(runs):
            totals = [t + r for t, r in zip(totals, run(flag, seed))]
        d, a, p, s, m, ate, mid, rev, esc = [t / runs for t in totals]
        print(f"{label:>16} {d:>7.1f} {p:>6.1f} {m:>7.0f} "
              f"{s:>5.0f} {ate:>5.0f} {mid:>5.0f} {rev:>5.0f} {esc:>5.0f}")