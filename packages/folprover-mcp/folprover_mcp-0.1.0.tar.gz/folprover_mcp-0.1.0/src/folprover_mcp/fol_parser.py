"""
First-Order Logic Parser

Parses FOL formulas with support for:
- Quantifiers: ∀ (forall), ∃ (exists)
- Logical operators: ∧ (and), ∨ (or), → (implies), ↔ (iff), ¬ (not), ⊕ (xor)
- Predicates: P(x, y, ...)
- Constants and Variables

Based on teacherpeterpan/Logic-LLM implementation.
"""

import re
from typing import Optional, Set, Tuple
import nltk
from nltk import Tree


class FOLParser:
    """Parser for First-Order Logic formulas."""

    def __init__(self) -> None:
        self.op_ls = ['⊕', '∨', '∧', '→', '↔', '∀', '∃', '¬', '(', ')', ',']
        self.sym_reg = re.compile(r'[^⊕∨∧→↔∀∃¬(),]+')

        # Context-free grammar template for FOL
        self.cfg_template = """
        S -> F | Q F | '¬' S | '(' S ')'
        Q -> QUANT VAR | QUANT VAR Q
        F -> '¬' '(' F ')' | '(' F ')' | F OP F | L
        OP -> '⊕' | '∨' | '∧' | '→' | '↔'
        L -> '¬' PRED '(' TERMS ')' | PRED '(' TERMS ')'
        TERMS -> TERM | TERM ',' TERMS
        TERM -> CONST | VAR
        QUANT -> '∀' | '∃'
        """

    def parse_text_fol_to_tree(self, rule_str: str) -> Tree:
        """Parse a FOL formula string into an NLTK tree."""
        r, parsed_fol_str = self.msplit(rule_str)
        cfg_str = self.make_cfg_str(r)

        grammar = nltk.CFG.fromstring(cfg_str)
        parser = nltk.ChartParser(grammar)
        tree = parser.parse_one(r)

        return tree

    def reorder_quantifiers(self, rule_str: str) -> str:
        """Reorder quantifiers to the front of the formula."""
        matches = re.findall(r'[∃∀]\w', rule_str)
        for match in matches[::-1]:
            rule_str = '%s ' % match + rule_str.replace(match, '', 1)
        return rule_str

    def msplit(self, s: str) -> Tuple[list, str]:
        """Split a FOL formula into tokens."""
        for op in self.op_ls:
            s = s.replace(op, ' %s ' % op)
        r = [e.strip() for e in s.split()]
        r = [e.replace('\'', '') for e in r]
        r = [e for e in r if e != '']

        res = []
        cur_str_ls = []
        for e in r:
            if (len(e) > 1) and self.sym_reg.match(e):
                cur_str_ls.append(e[0].upper() + e[1:])
            else:
                if len(cur_str_ls) > 0:
                    res.extend([''.join(cur_str_ls), e])
                else:
                    res.extend([e])
                cur_str_ls = []
        if len(cur_str_ls) > 0:
            res.append(''.join(cur_str_ls))

        make_str_ls = []
        for ind, e in enumerate(r):
            if re.match(r'[⊕∨∧→↔]', e):
                make_str_ls.append(' %s ' % e)
            elif re.match(r',', e):
                make_str_ls.append('%s ' % e)
            elif (len(e) == 1) and re.match(r'\w', e):
                if ((ind - 1) >= 0) and ((r[ind-1] == '∃') or (r[ind-1] == '∀')):
                    make_str_ls.append('%s ' % e)
                else:
                    make_str_ls.append(e)
            else:
                make_str_ls.append(e)

        return res, ''.join(make_str_ls)

    def make_cfg_str(self, token_ls: list) -> str:
        """Generate a CFG string with dynamic terminals."""
        sym_ls = list(set([e for e in token_ls if self.sym_reg.match(e)]))
        sym_str = ' | '.join(["'%s'" % s for s in sym_ls])
        cfg_str = self.cfg_template + 'VAR -> %s\nPRED -> %s\nCONST -> %s' % (sym_str, sym_str, sym_str)
        return cfg_str

    def find_variables(self, lvars: Set[str], tree) -> None:
        """Find all variables in a parse tree."""
        if isinstance(tree, str):
            return

        if tree.label() == 'VAR':
            lvars.add(tree[0])
            return

        for child in tree:
            self.find_variables(lvars, child)

    def symbol_resolution(self, tree: Tree) -> Tuple[Set[str], Set[str], Set[str]]:
        """Resolve symbols into variables, constants, and predicates."""
        lvars, consts, preds = set(), set(), set()
        self.find_variables(lvars, tree)
        self.preorder_resolution(tree, lvars, consts, preds)
        return lvars, consts, preds

    def preorder_resolution(self, tree, lvars: Set[str], consts: Set[str], preds: Set[str]) -> None:
        """Perform preorder traversal to resolve symbols."""
        if isinstance(tree, str):
            return

        if tree.label() == 'PRED':
            preds.add(tree[0])
            return

        if tree.label() == 'TERM':
            sym = tree[0][0]
            if sym in lvars:
                tree[0].set_label('VAR')
            else:
                tree[0].set_label('CONST')
                consts.add(sym)
            return

        for child in tree:
            self.preorder_resolution(child, lvars, consts, preds)


class FOLFormula:
    """Represents a parsed FOL formula."""

    def __init__(self, formula_str: str) -> None:
        self.formula_str = formula_str.strip()
        self.parser = FOLParser()
        self.tree: Optional[Tree] = None
        self.variables: Set[str] = set()
        self.constants: Set[str] = set()
        self.predicates: Set[str] = set()
        self.valid = False
        self.error_msg: Optional[str] = None

        self._parse()

    def _parse(self) -> None:
        """Parse the formula string."""
        try:
            self.tree = self.parser.parse_text_fol_to_tree(self.formula_str)
            self.variables, self.constants, self.predicates = self.parser.symbol_resolution(self.tree)
            self.valid = True
        except Exception as e:
            self.valid = False
            self.error_msg = str(e)

    def is_valid(self) -> bool:
        """Check if the formula was parsed successfully."""
        return self.valid

    def __str__(self) -> str:
        return self.formula_str

    def get_info(self) -> dict:
        """Get information about the parsed formula."""
        return {
            "formula": self.formula_str,
            "valid": self.valid,
            "error": self.error_msg,
            "variables": list(self.variables) if self.valid else [],
            "constants": list(self.constants) if self.valid else [],
            "predicates": list(self.predicates) if self.valid else [],
        }
