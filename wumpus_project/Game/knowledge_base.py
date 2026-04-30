# game/knowledge_base.py
# ─────────────────────────────────────────────────────────────
# Propositional Logic Knowledge Base with Resolution Refutation.
#
# Core concepts
# ─────────────
# • Literal  : a propositional variable ('P_1_2') or its
#              negation ('NOT_P_1_2').
# • Clause   : a disjunction (OR) of literals stored as a
#              frozenset so that {A, B} == {B, A}.
# • KB       : a set of clauses (conjunction of disjunctions –
#              Conjunctive Normal Form).
# • tell()   : assert new clauses into the KB.
# • ask()    : use Resolution Refutation to prove a query.
#              We negate the query, add it to a working copy of
#              the KB, then repeatedly resolve pairs of clauses.
#              If we ever derive the empty clause (⊥) we have a
#              contradiction → the original query is proved.
# ─────────────────────────────────────────────────────────────

from __future__ import annotations
from .utils import negate, get_neighbors


class Clause:
    """An immutable disjunction of literals (frozenset for O(1) hashing)."""

    def __init__(self, literals: list[str] | frozenset[str]) -> None:
        self.literals: frozenset[str] = frozenset(literals)

    # ── Equality / hashing ───────────────────────────────────
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Clause) and self.literals == other.literals

    def __hash__(self) -> int:
        return hash(self.literals)

    def __repr__(self) -> str:
        return "{" + ", ".join(sorted(self.literals)) + "}"

    # ── Helpers ──────────────────────────────────────────────
    def is_tautology(self) -> bool:
        """True if the clause contains both L and ¬L (always satisfied)."""
        for lit in self.literals:
            if negate(lit) in self.literals:
                return True
        return False

    def is_empty(self) -> bool:
        """The empty clause ⊥ – represents a contradiction."""
        return len(self.literals) == 0


def resolve(c1: Clause, c2: Clause) -> set[Clause]:
    """
    Binary resolution of two clauses.

    For every literal L in c1 whose complement ¬L appears in c2,
    produce a new resolvent clause:
        (c1 − {L}) ∪ (c2 − {¬L})

    Tautological resolvents are discarded.
    """
    resolvents: set[Clause] = set()
    for lit in c1.literals:
        neg = negate(lit)
        if neg in c2.literals:
            merged = (c1.literals - {lit}) | (c2.literals - {neg})
            new_clause = Clause(merged)
            if not new_clause.is_tautology():
                resolvents.add(new_clause)
    return resolvents


class KnowledgeBase:
    """
    A propositional-logic KB stored in CNF.

    Public interface
    ────────────────
    tell(clauses)          – add a list of Clause objects
    tell_fact(literal)     – assert a single literal as a unit clause
    ask(query_literals)    – Resolution Refutation; returns
                             (proved: bool, steps: int, log: list[str])
    add_breeze_rule(r,c)   – encode B(r,c) ⟺ ⋁ P(neighbors)
    add_stench_rule(r,c)   – encode S(r,c) ⟺ ⋁ W(neighbors)
    add_no_breeze(r,c)     – encode ¬B(r,c) → ¬P(n) for all neighbors n
    add_no_stench(r,c)     – encode ¬S(r,c) → ¬W(n) for all neighbors n
    """

    # Maximum resolution steps before giving up (prevents infinite loops
    # on queries the KB cannot decide).
    MAX_STEPS: int = 5_000

    def __init__(self) -> None:
        self.clauses: set[Clause] = set()
        self.inference_steps: int = 0   # cumulative counter across all asks

    # ── Assertion ────────────────────────────────────────────

    def tell(self, clauses: list[Clause]) -> None:
        """Add a list of clauses to the KB (non-tautological ones only)."""
        for clause in clauses:
            if not clause.is_tautology():
                self.clauses.add(clause)

    def tell_fact(self, literal: str) -> None:
        """Assert a single literal as a unit clause {literal}."""
        self.clauses.add(Clause([literal]))

    # ── Resolution Refutation ────────────────────────────────

    def ask(
        self, query_literals: list[str]
    ) -> tuple[bool, int, list[str]]:
        """
        Prove that the conjunction of query_literals follows from the KB.

        Strategy (Resolution Refutation / Proof by Contradiction):
          1. Negate each query literal and add as unit clauses to a
             working copy of the KB.
          2. Repeatedly pick pairs of clauses and resolve them.
          3. If ⊥ (empty clause) is derived → contradiction → query proved.
          4. If no new clauses can be generated → query cannot be proved.

        Returns
        ───────
        proved       : bool
        steps        : int   (resolution pairs attempted this call)
        log          : list[str]  (human-readable proof trace)
        """
        log: list[str] = []
        steps: int = 0

        # Step 1 – negate the query
        negated = [Clause([negate(lit)]) for lit in query_literals]
        log.append(f"Query literals : {query_literals}")
        log.append(f"Negated query  : {[str(c) for c in negated]}")

        # Working set = KB ∪ negated query
        working: set[Clause] = set(self.clauses)
        for c in negated:
            working.add(c)

        seen: set[Clause] = set(working)

        # Step 2 – resolution loop
        while True:
            clauses_list = list(working)
            new: set[Clause] = set()

            for i in range(len(clauses_list)):
                for j in range(i + 1, len(clauses_list)):
                    resolvents = resolve(clauses_list[i], clauses_list[j])
                    steps += 1

                    for r in resolvents:
                        if r.is_empty():
                            # Step 3 – contradiction found → PROVED
                            self.inference_steps += steps
                            log.append(
                                f"Empty clause derived after {steps} "
                                f"resolution steps → PROVED ✓"
                            )
                            return True, steps, log

                        if r not in seen:
                            new.add(r)
                            seen.add(r)

            # Step 4 – no new clauses → cannot prove
            if not new:
                self.inference_steps += steps
                log.append(
                    f"No new clauses after {steps} steps → "
                    f"CANNOT PROVE (query may be false or undecidable)"
                )
                return False, steps, log

            working |= new

            # Safety valve
            if steps > self.MAX_STEPS:
                self.inference_steps += steps
                log.append(f"Step limit ({self.MAX_STEPS}) reached → TIMEOUT")
                return False, steps, log

    # ── Domain-specific KB construction ──────────────────────

    def add_breeze_rule(self, r: int, c: int, rows: int, cols: int) -> None:
        """
        Encode  B(r,c) ⟺ ⋁ { P(n) | n is a neighbor of (r,c) }

        CNF decomposition
        ─────────────────
        Forward  (B → disjunction of pits):
            ¬B(r,c) ∨ P(n1) ∨ P(n2) ∨ …   [one clause]

        Backward (each pit implies breeze):
            ¬P(ni) ∨ B(r,c)               [one clause per neighbor]
        """
        neighbors = get_neighbors(r, c, rows, cols)
        pit_lits = [f"P_{nr}_{nc}" for nr, nc in neighbors]
        b = f"B_{r}_{c}"

        if pit_lits:
            # B → (P_n1 ∨ … ∨ P_nk)
            self.tell([Clause([negate(b)] + pit_lits)])
        # P_ni → B
        for p in pit_lits:
            self.tell([Clause([negate(p), b])])

    def add_stench_rule(self, r: int, c: int, rows: int, cols: int) -> None:
        """
        Encode  S(r,c) ⟺ ⋁ { W(n) | n is a neighbor of (r,c) }
        """
        neighbors = get_neighbors(r, c, rows, cols)
        w_lits = [f"W_{nr}_{nc}" for nr, nc in neighbors]
        s = f"S_{r}_{c}"

        if w_lits:
            self.tell([Clause([negate(s)] + w_lits)])
        for w in w_lits:
            self.tell([Clause([negate(w), s])])

    def add_no_breeze(self, r: int, c: int, rows: int, cols: int) -> None:
        """
        ¬B(r,c) → ¬P(n) for every neighbor n.
        (No breeze here means no adjacent pit.)
        """
        for nr, nc in get_neighbors(r, c, rows, cols):
            self.tell([Clause([f"NOT_P_{nr}_{nc}"])])

    def add_no_stench(self, r: int, c: int, rows: int, cols: int) -> None:
        """
        ¬S(r,c) → ¬W(n) for every neighbor n.
        """
        for nr, nc in get_neighbors(r, c, rows, cols):
            self.tell([Clause([f"NOT_W_{nr}_{nc}"])])
