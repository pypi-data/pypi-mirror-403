"""
Simple Built-in FOL Prover

A basic resolution-based prover for simple first-order logic problems.
This serves as a fallback when external provers (Vampire, E) are not available.

Note: This is a simplified implementation for demonstration and testing.
For complex proofs, use Vampire or E prover.
"""

from dataclasses import dataclass
from typing import List, Set, Optional, Tuple, Dict
import re
from enum import Enum


class SimpleProofResult(Enum):
    THEOREM = "Theorem"
    NOT_THEOREM = "NotTheorem"
    UNKNOWN = "Unknown"


@dataclass
class Literal:
    """A literal (atomic formula or its negation)."""
    predicate: str
    args: List[str]
    negated: bool = False

    def __str__(self):
        neg = "¬" if self.negated else ""
        args_str = ", ".join(self.args)
        return f"{neg}{self.predicate}({args_str})"

    def __hash__(self):
        return hash((self.predicate, tuple(self.args), self.negated))

    def __eq__(self, other):
        if not isinstance(other, Literal):
            return False
        return (self.predicate == other.predicate and
                self.args == other.args and
                self.negated == other.negated)

    def complement(self) -> 'Literal':
        """Return the complement of this literal."""
        return Literal(self.predicate, self.args, not self.negated)

    def is_ground(self) -> bool:
        """Check if this literal contains no variables."""
        return all(not self._is_variable(arg) for arg in self.args)

    @staticmethod
    def _is_variable(term: str) -> bool:
        """Variables start with lowercase and are single letters."""
        return len(term) == 1 and term.islower()


@dataclass
class Clause:
    """A disjunction of literals (CNF clause)."""
    literals: Set[Literal]

    def __str__(self):
        if not self.literals:
            return "⊥"  # Empty clause (contradiction)
        return " ∨ ".join(str(lit) for lit in self.literals)

    def __hash__(self):
        return hash(frozenset(self.literals))

    def __eq__(self, other):
        if not isinstance(other, Clause):
            return False
        return self.literals == other.literals

    def is_empty(self) -> bool:
        """Empty clause represents contradiction."""
        return len(self.literals) == 0

    def is_tautology(self) -> bool:
        """Check if clause contains a literal and its complement."""
        for lit in self.literals:
            if lit.complement() in self.literals:
                return True
        return False


class SimpleResolutionProver:
    """
    A simple resolution-based theorem prover for ground (variable-free) formulas.

    Uses the resolution principle: from (A ∨ B) and (¬A ∨ C), derive (B ∨ C).
    """

    def __init__(self, max_iterations: int = 1000):
        self.max_iterations = max_iterations

    def parse_literal(self, formula: str) -> Optional[Literal]:
        """Parse a simple literal like 'P(x, y)' or '¬P(x)'."""
        formula = formula.strip()

        negated = False
        if formula.startswith('¬') or formula.startswith('~') or formula.startswith('-'):
            negated = True
            formula = formula[1:].strip()

        # Match predicate(args)
        match = re.match(r'(\w+)\(([^)]*)\)', formula)
        if not match:
            return None

        predicate = match.group(1)
        args_str = match.group(2)
        args = [a.strip() for a in args_str.split(',')] if args_str else []

        return Literal(predicate, args, negated)

    def parse_clause(self, formula: str) -> Optional[Clause]:
        """Parse a clause (disjunction of literals)."""
        # Split by ∨ or |
        parts = re.split(r'\s*[∨|]\s*', formula)
        literals = set()

        for part in parts:
            lit = self.parse_literal(part.strip())
            if lit:
                literals.add(lit)

        return Clause(literals) if literals else None

    def negate_literal(self, lit: Literal) -> Literal:
        """Negate a literal."""
        return lit.complement()

    def resolve(self, clause1: Clause, clause2: Clause) -> Optional[Clause]:
        """
        Attempt to resolve two clauses.
        Returns the resolvent if resolution is possible, None otherwise.
        """
        for lit1 in clause1.literals:
            complement = lit1.complement()
            if complement in clause2.literals:
                # Found complementary literals
                new_literals = (clause1.literals - {lit1}) | (clause2.literals - {complement})
                resolvent = Clause(new_literals)

                # Don't return tautologies
                if not resolvent.is_tautology():
                    return resolvent

        return None

    def prove_by_resolution(self, clauses: List[Clause]) -> Tuple[SimpleProofResult, List[str]]:
        """
        Attempt to prove unsatisfiability using resolution.

        Returns:
            (result, derivation_steps)
        """
        all_clauses = set(clauses)
        new_clauses: Set[Clause] = set()
        derivation = []

        for i, c in enumerate(clauses):
            derivation.append(f"[{i}] {c} (given)")

        clause_list = list(all_clauses)
        iterations = 0

        while iterations < self.max_iterations:
            iterations += 1

            # Try all pairs
            for i, c1 in enumerate(clause_list):
                for j, c2 in enumerate(clause_list):
                    if i >= j:
                        continue

                    resolvent = self.resolve(c1, c2)
                    if resolvent is not None:
                        if resolvent.is_empty():
                            derivation.append(f"[{len(clause_list)}] ⊥ (resolve [{i}], [{j}])")
                            return SimpleProofResult.THEOREM, derivation

                        if resolvent not in all_clauses:
                            new_clauses.add(resolvent)

            if not new_clauses:
                # No new clauses can be derived
                return SimpleProofResult.NOT_THEOREM, derivation

            for nc in new_clauses:
                derivation.append(f"[{len(clause_list)}] {nc} (derived)")
                clause_list.append(nc)
                all_clauses.add(nc)

            new_clauses.clear()

        return SimpleProofResult.UNKNOWN, derivation

    def prove(
        self,
        premises: List[str],
        conclusion: str
    ) -> Tuple[SimpleProofResult, List[str]]:
        """
        Prove by refutation: add negation of conclusion and try to derive contradiction.

        Note: This simple prover only handles ground clauses (no variables).
        """
        clauses = []

        # Parse premises
        for premise in premises:
            clause = self.parse_clause(premise)
            if clause:
                clauses.append(clause)
            else:
                # Try as single literal
                lit = self.parse_literal(premise)
                if lit:
                    clauses.append(Clause({lit}))

        # Negate conclusion and add
        conc_lit = self.parse_literal(conclusion)
        if conc_lit:
            negated_conc = Clause({self.negate_literal(conc_lit)})
            clauses.append(negated_conc)
        else:
            # Try parsing as clause (would need more complex negation)
            return SimpleProofResult.UNKNOWN, ["Cannot parse conclusion"]

        if not clauses:
            return SimpleProofResult.UNKNOWN, ["No clauses to process"]

        return self.prove_by_resolution(clauses)


# Test cases
if __name__ == "__main__":
    prover = SimpleResolutionProver()

    # Test: Modus Ponens
    # P(a) and P(a) → Q(a) should derive Q(a)
    # In CNF: P(a), ¬P(a) ∨ Q(a)
    print("Test 1: Modus Ponens")
    premises = ["P(a)", "¬P(a) ∨ Q(a)"]
    conclusion = "Q(a)"
    result, steps = prover.prove(premises, conclusion)
    print(f"Result: {result.value}")
    for step in steps:
        print(f"  {step}")
    print()

    # Test: Syllogism
    print("Test 2: Syllogism")
    premises = ["Human(socrates)", "¬Human(socrates) ∨ Mortal(socrates)"]
    conclusion = "Mortal(socrates)"
    result, steps = prover.prove(premises, conclusion)
    print(f"Result: {result.value}")
    for step in steps:
        print(f"  {step}")
