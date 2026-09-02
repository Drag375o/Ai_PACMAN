# The maze layout and grid helpers. No Pygame here on purpose.

# Legend:
#   '#' = wall
#   '.' = pellet
#   'P' = Pac-Man start
#   'G' = ghost start
#   ' ' = empty walkable cell
MAZE = [
    "#####################",
    "#..................G#",
    "#.###.####.####.###.#",
    "#.###.####.####.###.#",
    "#...................#",
    "#.###.####.####.###.#",
    "#.###.####.####.###.#",
    "#...................#",
    "#.###.####.####.###.#",
    "#.###.####.####.###.#",
    "#...................#",
    "#.###.####.####.###.#",
    "#.###.####.####.###.#",
    "#P.................G#",
    "#####################",
]

CELL_SIZE = 30                 # pixels per grid cell
ROWS = len(MAZE)               # 15
COLS = len(MAZE[0])            # 21

# Four cardinal directions as (row delta, col delta). No diagonals.
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def is_wall(row, col):
    # True if the cell is a wall or outside the grid.
    # Treating out-of-bounds as a wall saves bounds checks elsewhere.
    if row < 0 or row >= ROWS or col < 0 or col >= COLS:
        return True
    return MAZE[row][col] == "#"


def neighbors(row, col):
    # All walkable cells adjacent to (row, col).
    # Used by the ghost, A*, and BFS - one definition of a legal move.
    result = []
    for d_row, d_col in DIRECTIONS:
        n_row, n_col = row + d_row, col + d_col
        if not is_wall(n_row, n_col):
            result.append((n_row, n_col))
    return result


def manhattan(cell_a, cell_b):
    # Grid distance ignoring walls: vertical steps + horizontal steps.
    # This is also A*'s heuristic h(n). It matches the legal moves (no
    # diagonals) and never overestimates, which keeps A* optimal.
    return abs(cell_a[0] - cell_b[0]) + abs(cell_a[1] - cell_b[1])


def parse_maze():
    # Read the layout once and extract the dynamic game state.
    # MAZE itself is never modified - it is the static map.
    # Returns: (pellets set, pacman start cell, list of ghost start cells)
    pellets = set()
    pacman_start = None
    ghost_starts = []

    for row in range(ROWS):
        for col in range(COLS):
            char = MAZE[row][col]
            if char == ".":
                pellets.add((row, col))
            elif char == "P":
                pacman_start = (row, col)
            elif char == "G":
                ghost_starts.append((row, col))

    return pellets, pacman_start, ghost_starts