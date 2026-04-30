# game/utils.py
# ─────────────────────────────────────────────────────────────
# Shared helper utilities used across the game package.
# ─────────────────────────────────────────────────────────────


def get_neighbors(r: int, c: int, rows: int, cols: int) -> list[tuple[int, int]]:
    """
    Return the valid orthogonal neighbors of cell (r, c)
    within a grid of size rows × cols.
    """
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            neighbors.append((nr, nc))
    return neighbors


def negate(literal: str) -> str:
    """
    Return the logical negation of a literal.
    e.g.  'P_1_2'     → 'NOT_P_1_2'
          'NOT_P_1_2' → 'P_1_2'
    """
    if literal.startswith("NOT_"):
        return literal[4:]
    return "NOT_" + literal


def bfs_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    passable: set[tuple[int, int]],
    rows: int,
    cols: int,
) -> list[tuple[int, int]]:
    """
    BFS shortest path from start → goal through cells in `passable`.
    Returns the full path (inclusive) or [start, goal] as a fallback.
    """
    from collections import deque

    if start == goal:
        return [start]

    queue: deque[list] = deque([[start]])
    seen: set = {start}

    while queue:
        path = queue.popleft()
        cur = path[-1]
        for nb in get_neighbors(*cur, rows, cols):
            if nb == goal:
                return path + [nb]
            if nb in passable and nb not in seen:
                seen.add(nb)
                queue.append(path + [nb])

    # Fallback: direct jump (caller must handle)
    return [start, goal]
