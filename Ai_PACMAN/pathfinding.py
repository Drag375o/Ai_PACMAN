# A* pathfinding and BFS. Pure logic - deliberately no Pygame import.
#
# Vocabulary:
#   node  : one grid cell, e.g. (13, 1)
#   g(n)  : cost actually spent getting from start to n   (a fact)
#   h(n)  : estimated remaining cost from n to the goal   (a guess)
#   f(n)  : g(n) + h(n) - estimated total cost of a route through n
#
# A* always expands the frontier node with the lowest f.

import heapq
from collections import deque
from maze import neighbors, manhattan, is_wall


def find_path_costed(start, goal, cell_cost=None):
    # A* where entering a cell costs 1 PLUS an optional extra from cell_cost.
    # cell_cost(cell) -> extra cost of stepping into that cell (0 or more).
    # With no cell_cost this is plain shortest-path A*.
    #
    # Manhattan stays admissible because the cheapest possible step is still 1,
    # so the estimate can never exceed the true remaining cost. A* therefore
    # still returns an optimal route - optimal in risk-adjusted cost, not steps.
    #
    # Returns (path, total_cost), or (None, None) if unreachable.
    if is_wall(*start) or is_wall(*goal):
        return None, None
    if start == goal:
        return [start], 0

    # The frontier: a min-heap of (f, g, node). heapq pops the smallest f.
    frontier = [(manhattan(start, goal), 0, start)]

    # Best known g for each node, and the node we arrived from.
    g_score = {start: 0}
    came_from = {}

    # Nodes already expanded, so we never process one twice.
    visited = set()

    while frontier:
        _, g, current = heapq.heappop(frontier)

        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            return _rebuild_path(came_from, start, goal), g

        for neighbor in neighbors(*current):
            extra = cell_cost(neighbor) if cell_cost else 0
            new_g = g + 1 + extra
            # Only keep this route if it beats the best one found so far.
            if new_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = new_g
                came_from[neighbor] = current
                f = new_g + manhattan(neighbor, goal)
                heapq.heappush(frontier, (f, new_g, neighbor))

    return None, None              # goal unreachable


def find_path(start, goal):
    # Plain shortest path, ignoring danger. Used by the Stage 5 tests.
    path, _ = find_path_costed(start, goal)
    return path


def _rebuild_path(came_from, start, goal):
    # Walk the came_from links backwards from goal to start, then flip.
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


def distance_map(source):
    # Breadth-first flood fill from source.
    # Returns {cell: steps} - true wall-aware distance to EVERY reachable cell.
    #
    # One BFS instead of one A* per cell: A* answers "how do I reach this one
    # place", BFS answers "how far is everywhere from here".
    distances = {source: 0}
    queue = deque([source])
    while queue:
        current = queue.popleft()
        for neighbor in neighbors(*current):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return distances