"""
TPTP Format Converter

Converts FOL formulas to TPTP format for use with Vampire and E provers.
TPTP (Thousands of Problems for Theorem Provers) is a standard format for ATP systems.
"""

import re
from typing import List, Optional, Tuple


class TPTPConverter:
    """Converts FOL formulas to TPTP format."""

    # Mapping from Unicode operators to TPTP operators
    OPERATOR_MAP = {
        '∧': '&',
        '∨': '|',
        '→': '=>',
        '↔': '<=>',
        '¬': '~',
        '⊕': '<~>',  # XOR in TPTP
        '∀': '!',
        '∃': '?',
    }

    def __init__(self):
        self.axiom_count = 0
        self.conjecture_count = 0

    def reset(self):
        """Reset formula counters."""
        self.axiom_count = 0
        self.conjecture_count = 0

    def convert_formula(self, formula: str) -> str:
        """
        Convert a single FOL formula from Unicode notation to TPTP syntax.

        Args:
            formula: FOL formula in Unicode notation

        Returns:
            Formula in TPTP syntax (without the fof wrapper)
        """
        result = formula

        # Replace Unicode operators with TPTP operators
        for unicode_op, tptp_op in self.OPERATOR_MAP.items():
            result = result.replace(unicode_op, tptp_op)

        # Handle quantifiers: ∀x P(x) -> ![X]: P(X)
        # Match quantifier patterns like !x, ?x
        result = self._convert_quantifiers(result)

        # Capitalize variables (TPTP convention: variables are uppercase)
        result = self._capitalize_variables(result)

        return result

    def _convert_quantifiers(self, formula: str) -> str:
        """Convert quantifier syntax to TPTP format."""
        # Pattern: !x or ?x followed by formula
        # Convert to ![X]: or ?[X]:

        # First, handle multiple quantifiers
        result = formula

        # Match quantifier followed by variable
        pattern = r'([!?])([a-z][a-z0-9]*)\s*'

        def replace_quantifier(match):
            quant = match.group(1)
            var = match.group(2).upper()
            return f'{quant}[{var}]: '

        result = re.sub(pattern, replace_quantifier, result, flags=re.IGNORECASE)

        return result

    def _capitalize_variables(self, formula: str) -> str:
        """
        Capitalize single-letter variables in the formula.
        TPTP convention: variables are uppercase, constants/predicates are lowercase.
        """
        # This is a simplified version - variables are typically single lowercase letters
        # We need to be careful not to capitalize predicate names

        result = formula

        # Find all words and capitalize single letters that appear as variables
        # Variables are typically bound by quantifiers or appear in predicate arguments

        # Pattern to find predicate calls: word(args)
        def process_args(match):
            pred = match.group(1)
            args = match.group(2)
            # Capitalize single-letter arguments
            new_args = re.sub(r'\b([a-z])\b', lambda m: m.group(1).upper(), args)
            return f'{pred}({new_args})'

        result = re.sub(r'(\w+)\(([^)]+)\)', process_args, result)

        return result

    def formula_to_axiom(self, formula: str, name: Optional[str] = None) -> str:
        """
        Convert a formula to a TPTP axiom.

        Args:
            formula: FOL formula in Unicode notation
            name: Optional name for the axiom

        Returns:
            Complete TPTP axiom statement
        """
        if name is None:
            self.axiom_count += 1
            name = f"axiom_{self.axiom_count}"

        tptp_formula = self.convert_formula(formula)
        return f"fof({name}, axiom, {tptp_formula})."

    def formula_to_conjecture(self, formula: str, name: Optional[str] = None) -> str:
        """
        Convert a formula to a TPTP conjecture (goal to prove).

        Args:
            formula: FOL formula in Unicode notation
            name: Optional name for the conjecture

        Returns:
            Complete TPTP conjecture statement
        """
        if name is None:
            self.conjecture_count += 1
            name = f"conjecture_{self.conjecture_count}"

        tptp_formula = self.convert_formula(formula)
        return f"fof({name}, conjecture, {tptp_formula})."

    def formula_to_negated_conjecture(self, formula: str, name: Optional[str] = None) -> str:
        """
        Convert a formula to a negated conjecture (for refutation proofs).

        Args:
            formula: FOL formula in Unicode notation
            name: Optional name for the negated conjecture

        Returns:
            Complete TPTP negated conjecture statement
        """
        if name is None:
            self.conjecture_count += 1
            name = f"negated_conjecture_{self.conjecture_count}"

        tptp_formula = self.convert_formula(formula)
        return f"fof({name}, negated_conjecture, ~({tptp_formula}))."

    def create_problem(
        self,
        premises: List[str],
        conclusion: str,
        problem_name: str = "problem"
    ) -> str:
        """
        Create a complete TPTP problem file.

        Args:
            premises: List of premise formulas in Unicode notation
            conclusion: Conclusion formula in Unicode notation
            problem_name: Name for the problem

        Returns:
            Complete TPTP problem as a string
        """
        self.reset()

        lines = [
            f"% TPTP Problem: {problem_name}",
            f"% Generated by FOL Prover MCP",
            "",
            "% Premises (Axioms)",
        ]

        for i, premise in enumerate(premises):
            axiom = self.formula_to_axiom(premise, f"premise_{i+1}")
            lines.append(axiom)

        lines.extend([
            "",
            "% Conclusion (Conjecture)",
            self.formula_to_conjecture(conclusion, "goal"),
        ])

        return "\n".join(lines)


class Prover9Converter:
    """Converts FOL formulas to Prover9 format."""

    # Mapping from Unicode operators to Prover9 operators
    OPERATOR_MAP = {
        '∧': '&',
        '∨': '|',
        '→': '->',
        '↔': '<->',
        '¬': '-',
        '⊕': None,  # XOR not directly supported, needs expansion
    }

    QUANTIFIER_MAP = {
        '∀': 'all',
        '∃': 'exists',
    }

    def convert_formula(self, formula: str) -> str:
        """
        Convert a single FOL formula from Unicode notation to Prover9 syntax.

        Args:
            formula: FOL formula in Unicode notation

        Returns:
            Formula in Prover9 syntax
        """
        result = formula

        # Handle quantifiers first: ∀x -> all x
        for unicode_q, prover9_q in self.QUANTIFIER_MAP.items():
            # Pattern: ∀x or ∃x
            pattern = rf'{unicode_q}(\w+)'
            result = re.sub(pattern, rf'{prover9_q} \1 ', result)

        # Replace Unicode operators with Prover9 operators
        for unicode_op, prover9_op in self.OPERATOR_MAP.items():
            if prover9_op is not None:
                result = result.replace(unicode_op, prover9_op)

        # Clean up extra spaces
        result = re.sub(r'\s+', ' ', result).strip()

        return result

    def create_problem(
        self,
        premises: List[str],
        conclusion: str
    ) -> str:
        """
        Create a complete Prover9 problem file.

        Args:
            premises: List of premise formulas in Unicode notation
            conclusion: Conclusion formula in Unicode notation

        Returns:
            Complete Prover9 problem as a string
        """
        lines = [
            "% Prover9 Problem",
            "% Generated by FOL Prover MCP",
            "",
            "formulas(assumptions).",
        ]

        for premise in premises:
            converted = self.convert_formula(premise)
            lines.append(f"    {converted}.")

        lines.extend([
            "end_of_list.",
            "",
            "formulas(goals).",
            f"    {self.convert_formula(conclusion)}.",
            "end_of_list.",
        ])

        return "\n".join(lines)
