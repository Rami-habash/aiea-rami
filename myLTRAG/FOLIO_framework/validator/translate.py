from .formula_format import *


# translate a common LaTeX-style formula to z3 form
def translate(formula):
    formula = "".join(formula.split())

    if contained(formula):
        formula = formula[1:-1]

    # if in predicate application form, do not translate
    if is_predicate(formula):
        return formula

    # if in existential or universal quantifier form
    if is_existential(formula) or is_forall(formula):
        if formula.startswith('(∀x)') or formula.startswith('(∃x)'):
            formula = formula[1:3] + formula[4:]
        quantifier = formula[0]
        if contained(formula[2:]):
            inner_formula = formula[3:-1].strip()
        else:
            inner_formula = formula[2:].strip()
        if quantifier == '∃':
            return f"Exists({formula[1]}, {translate(inner_formula)})"
        elif quantifier == '∀':
            return f"ForAll({formula[1]}, {translate(inner_formula)})"

    # equivalence, biconditional
    if is_equi(formula):
        equi_position, _ = is_equi(formula)
        left_formula = formula[:equi_position].strip()
        right_formula = formula[equi_position+1:].strip()
        if contained(left_formula):
            left_formula = left_formula[1:-1]
        if contained(right_formula):
            right_formula = right_formula[1:-1]
        # directly build And(Implies(...), Implies(...))
        return f"And(Implies({translate(left_formula)}, {translate(right_formula)}), Implies({translate(right_formula)}, {translate(left_formula)}))"

    # determine if it is implication form
    if is_implies(formula):
        implies_position, _ = is_implies(formula)
        left_formula = formula[:implies_position].strip()
        right_formula = formula[implies_position+1:].strip()
        if contained(left_formula):
            left_formula = left_formula[1:-1]
        if contained(right_formula):
            right_formula = right_formula[1:-1]
        return f"Implies({translate(left_formula)}, {translate(right_formula)})"

    # determine if it is disjunction form
    if is_disjunction(formula):
        disjunction_position, _ = is_disjunction(formula)
        left_formula = formula[:disjunction_position].strip()
        right_formula = formula[disjunction_position+1:].strip()
        if contained(left_formula):
            left_formula = left_formula[1:-1]
        if contained(right_formula):
            right_formula = right_formula[1:-1]
        return f"Or({translate(left_formula)}, {translate(right_formula)})"

    # determine if it is XOR form
    if is_xor(formula):
        xor_position, _ = is_xor(formula)
        left_formula = formula[:xor_position].strip()
        right_formula = formula[xor_position+1:].strip()
        if contained(left_formula):
            left_formula = left_formula[1:-1]
        if contained(right_formula):
            right_formula = right_formula[1:-1]
        return f"Xor({translate(left_formula)}, {translate(right_formula)})"

    # determine if it is conjunction form
    if is_conjunction(formula):
        conjunction_position, _ = is_conjunction(formula)
        left_formula = formula[:conjunction_position].strip()
        right_formula = formula[conjunction_position+1:].strip()
        if contained(left_formula):
            left_formula = left_formula[1:-1]
        if contained(right_formula):
            right_formula = right_formula[1:-1]
        return f"And({translate(left_formula)}, {translate(right_formula)})"

    # if it is negation form
    if is_negation(formula):
        inner_formula = formula[1:].strip()
        if contained(inner_formula):
            inner_formula = inner_formula[1:-1].strip()
        return f"Not({translate(inner_formula)})"

    # if other case, input error
    return f"-----{formula}-----"
