# AI Pac-Man - entry point: window, game loop, rendering.

import math
import random
import pygame
from maze import MAZE, CELL_SIZE, ROWS, COLS, is_wall, parse_maze, neighbors, manhattan
from pathfinding import distance_map
from ai import choose_target, DANGER_RADIUS

HUD_HEIGHT = 40
WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE + HUD_HEIGHT
FPS = 60

# Pac-Man moves one cell every MOVE_DELAY frames (60 / 8 = 7.5 cells per second)
MOVE_DELAY = 8

# Ghost settings
GHOST_MOVE_DELAY = 12          # slower than Pac-Man (8), so he can escape
CHASE_RADIUS = 8               # within this Manhattan distance, ghosts chase

STARTING_LIVES = 3
RESPAWN_PAUSE = 45             # frames frozen after losing a life

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
WALL_BLUE = (33, 33, 180)
YELLOW = (255, 235, 59)
PELLET = (245, 222, 179)
PATH_COLOR = (0, 120, 90)      # A* path overlay
TARGET_COLOR = (255, 60, 200)  # chosen pellet
GREEN = (120, 230, 120)
DANGER_COLOR = (190, 60, 60)   # danger zone; SIZE encodes severity, not shade
GHOST_COLORS = [(255, 70, 70), (255, 150, 40)]

# Arrow key -> (row delta, col delta). Down is +row because row is the y-axis.
KEY_DIRECTIONS = {
    pygame.K_UP: (-1, 0),
    pygame.K_DOWN: (1, 0),
    pygame.K_LEFT: (0, -1),
    pygame.K_RIGHT: (0, 1),
}


class PacMan:
    def __init__(self, start_cell):
        self.row, self.col = start_cell
        self.direction = (0, 0)
        self.move_timer = 0
        self.mouth_timer = 0
        self.score = 0
        self.lives = STARTING_LIVES
        # AI state
        self.ai_mode = True
        self.target = None     # the pellet we're heading for
        self.path = []         # remaining cells, next step first


class Ghost:
    def __init__(self, start_cell):
        self.row, self.col = start_cell
        self.direction = (0, 0)
        self.move_timer = 0
        self.mode = "RANDOM"   # shown in the HUD so we can see it switch


def cell_center(row, col):
    # Convert a grid cell to the pixel centre of that cell.
    return (col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2)


def update_pacman(pac, pellets):
    # MANUAL mode: advance one cell in the direction the player last pressed.
    pac.move_timer += 1
    if pac.move_timer < MOVE_DELAY:
        return
    pac.move_timer = 0

    d_row, d_col = pac.direction
    if (d_row, d_col) == (0, 0):
        return

    next_row = pac.row + d_row
    next_col = pac.col + d_col

    if is_wall(next_row, next_col):        # check BEFORE moving
        return

    pac.row, pac.col = next_row, next_col

    if (pac.row, pac.col) in pellets:
        pellets.remove((pac.row, pac.col))
        pac.score += 10


def update_ai_pacman(pac, pellets, ghost_distances):
    # AI mode: move one cell along the danger-aware A* path.
    pac.move_timer += 1
    if pac.move_timer < MOVE_DELAY:
        return
    pac.move_timer = 0

    # Replan when the plan is finished, the target is gone, or a ghost has
    # moved next to our next step. Replanning every single step instead was
    # measured as safer but far less decisive - see README.
    replan = not pac.path or pac.target not in pellets
    if not replan:
        next_cell = pac.path[0]
        for distances in ghost_distances:
            if distances.get(next_cell, 99) <= 1:
                replan = True
                break

    if replan:
        pac.target, path = choose_target(
            (pac.row, pac.col), pellets, ghost_distances
        )
        # Drop the first cell: it's where we already are.
        pac.path = path[1:] if path else []

    if not pac.path:
        return

    next_row, next_col = pac.path.pop(0)

    if is_wall(next_row, next_col):        # shouldn't happen; fail safe
        pac.path = []
        return

    # Direction must be computed BEFORE the position changes.
    pac.direction = (next_row - pac.row, next_col - pac.col)
    pac.row, pac.col = next_row, next_col

    if (pac.row, pac.col) in pellets:
        pellets.remove((pac.row, pac.col))
        pac.score += 10


def update_ghost(ghost, pac):
    # Random wander when far away, greedy step toward Pac-Man when close.
    # "Greedy" means it only looks one cell ahead. It has no plan, so walls
    # can trap it - unlike the A* Pac-Man. That contrast is the point.
    ghost.move_timer += 1
    if ghost.move_timer < GHOST_MOVE_DELAY:
        return
    ghost.move_timer = 0

    options = neighbors(ghost.row, ghost.col)
    if not options:
        return

    pac_cell = (pac.row, pac.col)
    distance = manhattan((ghost.row, ghost.col), pac_cell)

    if distance <= CHASE_RADIUS:
        ghost.mode = "CHASE"
        # Step to whichever neighbour is closest to Pac-Man.
        target = min(options, key=lambda cell: manhattan(cell, pac_cell))
    else:
        ghost.mode = "RANDOM"
        # Avoid turning straight back the way we came, unless it's a dead end,
        # otherwise the ghost vibrates between two cells and never travels.
        came_from = (ghost.row - ghost.direction[0], ghost.col - ghost.direction[1])
        forward_options = [cell for cell in options if cell != came_from]
        target = random.choice(forward_options or options)

    ghost.direction = (target[0] - ghost.row, target[1] - ghost.col)
    ghost.row, ghost.col = target


def draw_maze(screen):
    # Draw one rectangle per wall cell. Remember: col -> x, row -> y.
    for row in range(ROWS):
        for col in range(COLS):
            if is_wall(row, col):
                rect = pygame.Rect(
                    col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE
                )
                pygame.draw.rect(screen, WALL_BLUE, rect)


def draw_danger(screen, ghost_distances):
    # Show the ghosts' threat zones. Marker SIZE encodes severity - bigger and
    # thicker means more dangerous. Because these come from BFS, the zones
    # bend around walls instead of forming a diamond.
    for distances in ghost_distances:
        for (row, col), steps in distances.items():
            if steps == 0 or steps >= DANGER_RADIUS:
                continue
            severity = DANGER_RADIUS - steps        # 1..5
            size = 6 + severity * 4
            thickness = 1 if severity <= 2 else 2
            x, y = cell_center(row, col)
            rect = pygame.Rect(x - size // 2, y - size // 2, size, size)
            pygame.draw.rect(screen, DANGER_COLOR, rect, thickness)


def draw_pellets(screen, pellets):
    for row, col in pellets:
        pygame.draw.circle(screen, PELLET, cell_center(row, col), 3)


def draw_ai_plan(screen, pac):
    # Show the A* path and the chosen target - makes the AI visible.
    for row, col in pac.path:
        rect = pygame.Rect(
            col * CELL_SIZE + 10, row * CELL_SIZE + 10,
            CELL_SIZE - 20, CELL_SIZE - 20,
        )
        pygame.draw.rect(screen, PATH_COLOR, rect)

    if pac.target:
        pygame.draw.circle(screen, TARGET_COLOR, cell_center(*pac.target), 8, 3)


def draw_pacman(screen, pac):
    # Mouth opens and closes on a timer and points along the last direction.
    x, y = cell_center(pac.row, pac.col)
    radius = CELL_SIZE // 2 - 2
    openness = 0.35 if (pac.mouth_timer // 8) % 2 == 0 else 0.05

    d_row, d_col = pac.direction
    if (d_row, d_col) == (0, -1):
        facing = math.pi
    elif (d_row, d_col) == (-1, 0):
        facing = -math.pi / 2
    elif (d_row, d_col) == (1, 0):
        facing = math.pi / 2
    else:
        facing = 0.0                        # right, and the default at rest

    start = facing + openness
    end = facing + 2 * math.pi - openness
    points = [(x, y)]
    steps = 20
    for i in range(steps + 1):
        angle = start + (end - start) * i / steps
        points.append((x + radius * math.cos(angle), y + radius * math.sin(angle)))
    pygame.draw.polygon(screen, YELLOW, points)


def draw_ghost(screen, ghost, color):
    x, y = cell_center(ghost.row, ghost.col)
    radius = CELL_SIZE // 2 - 2
    # Rounded head plus a square body - a ghost silhouette from two shapes.
    pygame.draw.circle(screen, color, (x, y - 2), radius)
    pygame.draw.rect(screen, color, pygame.Rect(x - radius, y - 2, radius * 2, radius))


def draw_hud(screen, font, pac, pellets, ghosts):
    y = ROWS * CELL_SIZE + 10
    mode = "AI" if pac.ai_mode else "MANUAL"
    screen.blit(font.render(f"[{mode}]", True, GREEN if pac.ai_mode else WHITE), (8, y))

    modes = "/".join(g.mode[0] for g in ghosts)     # "C/R" etc
    info = (f"Score:{pac.score}  Lives:{pac.lives}  "
            f"Pellets:{len(pellets)}  Ghosts:{modes}")
    screen.blit(font.render(info, True, WHITE), (95, y))


def draw_overlay(screen, font, big_font, message, sub):
    veil = pygame.Surface((WIDTH, ROWS * CELL_SIZE))
    veil.set_alpha(200)
    veil.fill(BLACK)
    screen.blit(veil, (0, 0))

    text = big_font.render(message, True, YELLOW)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 50))
    hint = font.render(sub, True, WHITE)
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 5))


def new_game():
    # Build a fresh game state. Called at start and on restart.
    pellets, pacman_start, ghost_starts = parse_maze()
    pac = PacMan(pacman_start)
    ghosts = [Ghost(cell) for cell in ghost_starts]
    return pellets, pac, ghosts, pacman_start, ghost_starts


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AI Pac-Man")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 19)
    big_font = pygame.font.SysFont("consolas", 44, bold=True)

    pellets, pac, ghosts, pac_start, ghost_starts = new_game()
    state = "PLAYING"          # PLAYING / DEAD_PAUSE / GAME_OVER / WIN
    pause_timer = 0
    was_ai = pac.ai_mode

    running = True
    while running:
        # 1. EVENTS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    pac.ai_mode = not pac.ai_mode
                    was_ai = pac.ai_mode
                    pac.path = []
                    pac.target = None
                    pac.direction = (0, 0)
                elif event.key == pygame.K_r and state in ("GAME_OVER", "WIN"):
                    pellets, pac, ghosts, pac_start, ghost_starts = new_game()
                    pac.ai_mode = was_ai
                    state = "PLAYING"
                elif event.key in KEY_DIRECTIONS:
                    pac.direction = KEY_DIRECTIONS[event.key]

        # 2. UPDATE
        # One BFS per ghost gives wall-aware distances to every cell.
        ghost_distances = [distance_map((g.row, g.col)) for g in ghosts]

        if state == "DEAD_PAUSE":
            pause_timer -= 1
            if pause_timer <= 0:
                state = "PLAYING"

        elif state == "PLAYING":
            pac.mouth_timer += 1

            # Record positions BEFORE anyone moves, so we can detect a swap.
            pac_before = (pac.row, pac.col)
            ghosts_before = [(g.row, g.col) for g in ghosts]

            if pac.ai_mode:
                update_ai_pacman(pac, pellets, ghost_distances)
            else:
                update_pacman(pac, pellets)
            for ghost in ghosts:
                update_ghost(ghost, pac)

            pac_after = (pac.row, pac.col)

            # Two ways to be caught:
            #   a) landed on the same cell
            #   b) SWAPPED cells - passed straight through each other
            caught = False
            for ghost, before in zip(ghosts, ghosts_before):
                after = (ghost.row, ghost.col)
                if after == pac_after:
                    caught = True
                elif after == pac_before and before == pac_after:
                    caught = True                # the swap case
                if caught:
                    break

            if caught:
                pac.lives -= 1
                pac.path = []
                pac.target = None
                pac.direction = (0, 0)
                pac.row, pac.col = pac_start
                for ghost, cell in zip(ghosts, ghost_starts):
                    ghost.row, ghost.col = cell
                if pac.lives <= 0:
                    state = "GAME_OVER"
                else:
                    state = "DEAD_PAUSE"
                    pause_timer = RESPAWN_PAUSE

            elif not pellets:
                state = "WIN"

        # 3. DRAW
        screen.fill(BLACK)
        draw_maze(screen)
        draw_danger(screen, ghost_distances)
        draw_pellets(screen, pellets)
        if pac.ai_mode and state == "PLAYING":
            draw_ai_plan(screen, pac)       # over pellets, under Pac-Man
        draw_pacman(screen, pac)
        for i, ghost in enumerate(ghosts):
            draw_ghost(screen, ghost, GHOST_COLORS[i % len(GHOST_COLORS)])
        draw_hud(screen, font, pac, pellets, ghosts)

        if state == "GAME_OVER":
            draw_overlay(screen, font, big_font, "GAME OVER",
                         f"Score {pac.score}   -   press R to restart")
        elif state == "WIN":
            draw_overlay(screen, font, big_font, "MAZE CLEARED",
                         f"Score {pac.score}   -   press R to restart")

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()