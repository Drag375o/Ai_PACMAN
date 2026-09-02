"""Test A* without opening a game window."""

from collections import deque
from maze import MAZE, ROWS, COLS, neighbors, parse_maze, is_wall
from pathfinding import find_path


def show_path(path):
    """Print the maze with the path drawn as '*'."""
    grid = [list(row) for row in MAZE]
    for row, col in path:
        if grid[row][col] not in ("P", "G"):
            grid[row][col] = "*"
    for row in grid:
        print("".join(row))


def is_valid(path):
    """Every step must be adjacent and walkable."""
    for row, col in path:
        if is_wall(row, col):
            return False, f"path enters a wall at {(row, col)}"
    for a, b in zip(path, path[1:]):
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1:
            return False, f"non-adjacent jump {a} -> {b}"
    return True, "valid"


def count_explored_astar(start, goal):
    """Re-run A*'s loop just to count how many nodes it expanded."""
    import heapq
    from maze import manhattan
    frontier = [(manhattan(start, goal), 0, start)]
    g_score = {start: 0}
    visited = set()
    while frontier:
        _, g, current = heapq.heappop(frontier)
        if current in visited:
            continue
        visited.add(current)
        if current == goal:
            return len(visited)
        for nb in neighbors(*current):
            if g + 1 < g_score.get(nb, float("inf")):
                g_score[nb] = g + 1
                heapq.heappush(frontier, (g + 1 + manhattan(nb, goal), g + 1, nb))
    return len(visited)


def count_explored_bfs(start, goal):
    """Blind breadth-first search, for comparison."""
    queue = deque([start])
    visited = {start}
    while queue:
        current = queue.popleft()
        if current == goal:
            return len(visited)
        for nb in neighbors(*current):
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return len(visited)


pellets, pacman_start, ghost_starts = parse_maze()
ghost_start = ghost_starts[0]

print(f"Pac-Man starts at {pacman_start}, ghost at {ghost_start}")
print(f"Walkable cells in maze: {sum(1 for r in range(ROWS) for c in range(COLS) if not is_wall(r, c))}")
print(f"Pellets: {len(pellets)}\n")

print("--- TEST 1: corner to corner ---")
path = find_path(pacman_start, ghost_start)
print(f"Path length: {len(path)} cells = {len(path) - 1} steps")
print("Validity:", is_valid(path)[1])
show_path(path)

print("\n--- TEST 2: nodes explored, A* vs blind BFS ---")
a = count_explored_astar(pacman_start, ghost_start)
b = count_explored_bfs(pacman_start, ghost_start)
print(f"A* expanded {a} nodes")
print(f"BFS expanded {b} nodes")

print("\n--- TEST 3: same cell ---")
print(find_path(pacman_start, pacman_start))

print("\n--- TEST 4: goal is a wall (should be None) ---")
print(find_path(pacman_start, (0, 0)))

print("\n--- TEST 5: every pellet reachable? ---")
unreachable = [p for p in pellets if find_path(pacman_start, p) is None]
print(f"Unreachable pellets: {len(unreachable)}")


def count_expanded_bfs(start, goal):
    """Blind BFS, counting nodes EXPANDED (popped) — fair vs the A* count."""
    queue = deque([start])
    seen = {start}
    expanded = 0
    while queue:
        current = queue.popleft()
        expanded += 1
        if current == goal:
            return expanded
        for nb in neighbors(*current):
            if nb not in seen:
                seen.add(nb)
                queue.append(nb)
    return expanded


print("\n--- TEST 6: A* vs BFS on nearer goals (fair count) ---")
print(f"{'goal':>10} {'steps':>6} {'A*':>5} {'BFS':>5}  saving")
for goal in [(10, 5), (7, 10), (4, 15), (1, 19)]:
    path = find_path(pacman_start, goal)
    a = count_explored_astar(pacman_start, goal)
    b = count_expanded_bfs(pacman_start, goal)
    saving = f"{100 * (b - a) / b:.0f}%" if b else "-"
    print(f"{str(goal):>10} {len(path) - 1:>6} {a:>5} {b:>5}  {saving:>6}")