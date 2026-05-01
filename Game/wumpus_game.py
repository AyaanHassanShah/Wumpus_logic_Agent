# game/wumpus_game.py
# ─────────────────────────────────────────────────────────────
# WumpusGame  –  core game state, percept generation, and the
#                Knowledge-Based Agent's decision loop.
# ─────────────────────────────────────────────────────────────

from __future__ import annotations
import random
from .knowledge_base import KnowledgeBase
from .utils import get_neighbors, bfs_path


class WumpusGame:
    """
    Encapsulates one episode of the Wumpus World.

    Grid coordinates: (row, col), zero-indexed, origin at top-left.
    The agent always starts at (0, 0).

    Hazard placement
    ────────────────
    • Pits   : ~1/6 of all cells (minimum 1), placed randomly.
    • Wumpus : exactly one, placed randomly.
    • Gold   : placed randomly (never at start).
    All hazards are kept away from (0, 0).
    """

    def __init__(self, rows: int, cols: int) -> None:
        self.rows = rows
        self.cols = cols
        self.reset()

    # ── Lifecycle ────────────────────────────────────────────

    def reset(self) -> None:
        """Re-initialise a fresh episode (new random hazard layout)."""
        self.kb = KnowledgeBase()

        self.visited:          set[tuple[int, int]] = set()
        self.safe_cells:       set[tuple[int, int]] = set()
        self.confirmed_danger: set[tuple[int, int]] = set()

        self.percepts_log: list[str] = []
        self.agent_pos:    tuple[int, int] = (0, 0)
        self.alive:        bool = True
        self.won:          bool = False
        self.gold_collected: bool = False

        self._place_hazards()

        # The starting cell is known safe; visit it immediately.
        self.safe_cells.add((0, 0))
        self._visit(0, 0)

    def _place_hazards(self) -> None:
        """Randomly place pits, wumpus, and gold (never at origin)."""
        candidates = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) != (0, 0)
        ]
        random.shuffle(candidates)

        n_pits = max(1, (self.rows * self.cols) // 6)
        self.pits:   set[tuple[int, int]] = set(map(tuple, candidates[:n_pits]))
        self.wumpus: tuple[int, int] | None = (
            tuple(candidates[n_pits]) if len(candidates) > n_pits else None
        )
        self.gold: tuple[int, int] = (
            tuple(candidates[n_pits + 1])
            if len(candidates) > n_pits + 1
            else (self.rows - 1, self.cols - 1)
        )

    # ── Percept / visit logic ────────────────────────────────

    def _visit(self, r: int, c: int) -> list[str]:
        """
        Mark (r, c) as visited, generate percepts, and update the KB.
        Returns the list of active percept strings.
        """
        self.visited.add((r, c))
        self.safe_cells.add((r, c))
        percepts: list[str] = []

        # ── Breeze ──
        breeze = any(
            (r, c) in get_neighbors(pr, pc, self.rows, self.cols)
            for pr, pc in self.pits
        )
        if breeze:
            percepts.append("Breeze")
            self.kb.tell_fact(f"B_{r}_{c}")
            self.kb.add_breeze_rule(r, c, self.rows, self.cols)
        else:
            self.kb.tell_fact(f"NOT_B_{r}_{c}")
            self.kb.add_no_breeze(r, c, self.rows, self.cols)

        # ── Stench ──
        stench = bool(
            self.wumpus
            and (r, c) in get_neighbors(
                self.wumpus[0], self.wumpus[1], self.rows, self.cols
            )
        )
        if stench:
            percepts.append("Stench")
            self.kb.tell_fact(f"S_{r}_{c}")
            self.kb.add_stench_rule(r, c, self.rows, self.cols)
        else:
            self.kb.tell_fact(f"NOT_S_{r}_{c}")
            self.kb.add_no_stench(r, c, self.rows, self.cols)

        # ── Glitter (gold) ──
        if (r, c) == self.gold and not self.gold_collected:
            percepts.append("Glitter")
            self.gold_collected = True
            self.won = True

        self.kb.tell_fact(f"VISITED_{r}_{c}")
        self.percepts_log = percepts
        return percepts

    # ── KB query ─────────────────────────────────────────────

    def query_safe(
        self, r: int, c: int
    ) -> tuple[bool, int, list[str]]:
        """
        Ask the KB whether cell (r, c) is provably free of pits AND wumpus.

        Runs two Resolution Refutation proofs:
            1.  ¬P(r,c)   – no pit
            2.  ¬W(r,c)   – no wumpus
        Cell is safe iff both are proved.
        """
        no_pit,    s1, l1 = self.kb.ask([f"NOT_P_{r}_{c}"])
        no_wumpus, s2, l2 = self.kb.ask([f"NOT_W_{r}_{c}"])
        return no_pit and no_wumpus, s1 + s2, l1 + l2

    # ── Agent actions ────────────────────────────────────────

    def move(self, r: int, c: int) -> dict:
        """
        Attempt to move the agent to (r, c).
        The cell must be orthogonally adjacent to the current position.
        Returns the serialised game state.
        """
        if not self.alive or self.won:
            return self._state("Game already over.")

        if (r, c) not in get_neighbors(*self.agent_pos, self.rows, self.cols):
            return self._state("Invalid move: cell is not adjacent.")

        # Query KB before committing to the move
        is_safe, steps, log = self.query_safe(r, c)

        self.agent_pos = (r, c)

        # Check actual outcome
        if (r, c) in self.pits or (r, c) == self.wumpus:
            self.alive = False
            self.confirmed_danger.add((r, c))
            hazard = "pit" if (r, c) in self.pits else "Wumpus"
            return self._state(f"Agent stepped into a {hazard}! 💀", steps, log, is_safe)

        self._visit(r, c)
        return self._state(f"Moved to ({r},{c}).", steps, log, is_safe)

    def auto_step(self) -> dict:
        """
        Execute one automated step using the KB-guided strategy:

        Priority order
        ──────────────
        1. Move to an unvisited neighbor that the KB proves safe.
        2. Navigate (BFS) toward the nearest frontier cell that the
           KB proves safe (may require backtracking through visited cells).
        3. Brave move: unvisited neighbor not confirmed dangerous
           (KB uncertain – agent takes a calculated risk).
        4. Backtrack along visited cells.
        """
        if not self.alive or self.won:
            return self._state("Game over.")

        r, c = self.agent_pos
        neighbors = get_neighbors(r, c, self.rows, self.cols)
        unvisited_nb = [nb for nb in neighbors if nb not in self.visited]

        # ── Priority 1: KB-proven safe unvisited neighbor ──
        for nr, nc in unvisited_nb:
            is_safe, steps, log = self.query_safe(nr, nc)
            if is_safe:
                self.agent_pos = (nr, nc)
                self._visit(nr, nc)
                return self._state(
                    f"Auto-moved to ({nr},{nc}) — KB proved safe ✓",
                    steps, log, True
                )

        # ── Priority 2: Navigate to safe frontier via BFS ──
        frontier: list[tuple[tuple, tuple, int, list]] = []
        for vr, vc in self.visited:
            for nr, nc in get_neighbors(vr, vc, self.rows, self.cols):
                if (nr, nc) not in self.visited:
                    is_safe, steps, log = self.query_safe(nr, nc)
                    if is_safe:
                        frontier.append(((nr, nc), (vr, vc), steps, log))

        if frontier:
            target, via, steps, log = frontier[0]
            path = bfs_path(self.agent_pos, via, self.visited, self.rows, self.cols)
            next_step = path[1] if len(path) > 1 else via

            self.agent_pos = next_step
            if next_step not in self.visited:
                self._visit(*next_step)

            return self._state(
                f"Navigating toward safe frontier {target} — next step {next_step}",
                steps, log, True
            )

        # ── Priority 3: Brave move (KB uncertain) ──
        candidates = [
            nb for nb in unvisited_nb
            if nb not in self.confirmed_danger
        ]
        if candidates:
            target = candidates[0]
            self.agent_pos = target

            if target in self.pits or target == self.wumpus:
                self.alive = False
                self.confirmed_danger.add(target)
                return self._state(
                    f"Brave move to {target} — walked into danger! 💀",
                    0, ["Brave move; KB had no proof of safety."], False
                )

            self._visit(*target)
            return self._state(
                f"Brave move to {target} — KB uncertain, risk taken.",
                0, ["No proof of safety; brave/risky move taken."], False
            )

        # ── Priority 4: Backtrack ──
        visited_nb = [nb for nb in neighbors if nb in self.visited]
        if visited_nb:
            self.agent_pos = visited_nb[0]
            return self._state(f"Backtracked to {visited_nb[0]}.", 0, [], False)

        return self._state("No moves available — agent is stuck.", 0, [], False)

    # ── Serialisation ────────────────────────────────────────

    def _cell_status(self) -> dict[str, str]:
        """Return display status for every cell."""
        status: dict[str, str] = {}
        for row in range(self.rows):
            for col in range(self.cols):
                pos = (row, col)
                key = f"{row},{col}"
                if pos in self.confirmed_danger:
                    status[key] = "danger"
                elif pos == self.agent_pos:
                    status[key] = "agent"
                elif pos in self.visited:
                    status[key] = "visited"
                elif pos in self.safe_cells:
                    status[key] = "safe"
                else:
                    status[key] = "unknown"
        return status

    def _state(
        self,
        message: str = "",
        last_steps: int = 0,
        log: list[str] | None = None,
        was_safe_query: bool = False,
    ) -> dict:
        visited_count = len(self.visited)
        return {
            "rows":             self.rows,
            "cols":             self.cols,
            "agent":            list(self.agent_pos),
            "alive":            self.alive,
            "won":              self.won,
            "gold_collected":   self.gold_collected,
            "percepts":         self.percepts_log,
            "cell_states":      self._cell_status(),
            "inference_steps":  self.kb.inference_steps,
            "last_steps":       last_steps,
            "visited_count":    visited_count,
            "log":              log or [],
            "message":          message,
            "was_safe_query":   was_safe_query,
        }

    def get_state(self) -> dict:
        return self._state()

    def reveal_truth(self) -> dict:
        """Return the ground-truth positions of all hazards and gold."""
        return {
            "pits":   [list(p) for p in self.pits],
            "wumpus": list(self.wumpus) if self.wumpus else None,
            "gold":   list(self.gold),
        }
