from .auxiliary import *


# determine if formula is one of: predicate application, negation, conjunction, disjunction, XOR, implication, or quantifier form
def is_formula(formula):
    if contained(formula):
        formula = formula[1:-1]

    return is_predicate(formula) or \
            is_negation(formula) or \
            is_conjunction(formula) or \
            is_implies(formula) or\
            is_equi(formula) or \
            is_xor(formula) or\
            is_disjunction(formula) or \
            is_existential(formula) or \
            is_forall(formula)


# determine if a formula is predicate form (atomic formula)
def is_predicate(formula):
    formula = "".join(formula.split())
    if contained(formula):
        formula = formula[1:-1]

    # cannot start with quantifier or negation symbol
    if len(formula) > 0 and formula[0] in ['∃', '∀', '¬']:
       return False

    # can have at most one pair of parentheses
    num_of_paren = formula.count('(')
    if num_of_paren > 1:
        return False

    # if formula contains binary connective, return False
    if '→' in formula or '∧' in formula or '∨' in formula or '⊕' in formula or '↔' in formula:
        return False

    left_paren_index = 0
    if '(' in formula:
        left_paren_index = formula.index('(')

    # determine if there are matching parentheses
    if contained(formula[left_paren_index:-1]):
        return True

    # extract part between parentheses, should be predicate symbol
    predic = formula[:left_paren_index]

    # check if predicate symbol meets requirements (allow uppercase or lowercase first letter)
    if not (len(predic) > 0 and predic[0].isalpha()):
        return False

    return True


# determine if a formula is negation
def is_negation(formula):
    if not '¬' in formula:
        return False
    formula = "".join(formula.split())
    if contained(formula):
        formula = formula[1:-1]
    if not is_balanced_parentheses(formula):
        return False

    # check if formula starts with "¬"
    if formula.startswith('¬'):
        # if sub-formula starting from second symbol is enclosed, then it is negation form
        if contained(formula[1:]):
            return True

        # from second symbol, look for other connectives
        for i in range(1, len(formula)-1):
            if formula[i] in ['∧', '∨', '→', '⊕', '↔']:
                left_formula = formula[:i].strip()
                right_formula = formula[i+1:].strip()
                if is_formula(left_formula) and is_formula(right_formula):
                    return False
        return True
    return False
# is_negation


# determine if a formula is a conjunction
def is_conjunction(formula):
    if '∧' not in formula:
        return False
    if is_xor(formula) or is_disjunction(formula) or is_implies(formula):
        return False
    formula = "".join(formula.split())
    if contained(formula):
        formula = formula[1:-1]
    if not is_balanced_parentheses(formula):
        return False

    # find outermost ∧
    depth = 0
    for i, char in enumerate(formula):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == '∧' and depth == 0:
            left_formula = formula[:i].strip()
            right_formula = formula[i+1:].strip()
            return (i, True) if is_formula(left_formula) and is_formula(right_formula) else False
    return False



# determine if a formula is XOR
def is_xor(formula):
    if not '⊕' in formula:
        return False
    if is_disjunction(formula) or is_implies(formula):
        return False
    formula = "".join(formula.split())
    if contained(formula):
        formula = formula[1:-1]
    if not is_balanced_parentheses(formula):
        return False

    # check each ∧ symbol
    for i in range(len(formula)):
        if formula[i] == '⊕':
            # check if both sides of ∧ symbol are formulas
            left_formula = formula[:i].strip()
            if contained(left_formula):
                left_formula = left_formula[1:-1]
            right_formula = formula[i+1:].strip()
            if contained(right_formula):
                right_formula = right_formula[1:-1]

            # if both sides are formulas, it is a conjunction
            if is_formula(left_formula) and is_formula(right_formula):
                return (i, True)
    return False
# is_xor(formula)


# determine if a formula is disjunction
def is_disjunction(formula):
    if not '∨' in formula:
        return False
    if is_implies(formula):
        return False
    formula = "".join(formula.split())
    if contained(formula):
        formula = formula[1:-1]
    if not is_balanced_parentheses(formula):
        return False

    # check each ∨ symbol
    for i in range(len(formula)):
        if formula[i] == '∨':
            # check if both sides of ∨ symbol are formulas
            left_formula = formula[:i].strip()
            if contained(left_formula):
                left_formula = left_formula[1:-1]
            right_formula = formula[i+1:].strip()
            if contained(right_formula):
                right_formula = right_formula[1:-1]

            # if both sides are formulas, it is a disjunction
            if is_formula(left_formula) and is_formula(right_formula):
                return (i, True)
    return False
# is_disjunction(formula)


# determine if a formula is implication
def is_implies(formula):
    if '→' not in formula:
        return False
    if is_equi(formula):
        return False

    formula = "".join(formula.split())
    if contained(formula):
        formula = formula[1:-1]
    if not is_balanced_parentheses(formula):
        return False

    # find outermost →
    depth = 0
    for i, char in enumerate(formula):
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == '→' and depth == 0:
            left_formula = formula[:i].strip()
            right_formula = formula[i+1:].strip()
            return (i, True) if is_formula(left_formula) and is_formula(right_formula) else False

    return False


# determine if a formula is equivalence
def is_equi(formula):
    if not '↔' in formula:
        return False
    formula = "".join(formula.split())
    if contained(formula):
        formula = formula[1:-1]
    if not is_balanced_parentheses(formula):
        return False

    # use parenthesis count to correctly extract left and right sub-formulas
    equi_position = -1
    bracket_count = 0
    for i, char in enumerate(formula):
        if char == '(':
            bracket_count += 1
        elif char == ')':
            bracket_count -= 1
        if char == '↔' and bracket_count == 0:
            equi_position = i
            break

    if equi_position == -1:
        return False

    left_formula = formula[:equi_position].strip()
    right_formula = formula[equi_position+1:].strip()

    # remove outer parentheses
    if contained(left_formula):
        left_formula = left_formula[1:-1]
    if contained(right_formula):
        right_formula = right_formula[1:-1]

    # check if left and right sub-formulas are valid formulas
    if is_formula(left_formula) and is_formula(right_formula):
        return (equi_position, True)
    return False

# determine if a formula is existential form
def is_existential(formula):
    if not '∃' in formula:
        return False
    formula = "".join(formula.split())
    if formula.startswith('(∃x)'):
        formula = formula[1:3] + formula[4:]
    if contained(formula):
        formula = formula[1:-1]
    if not is_balanced_parentheses(formula):
        return False

    if formula.startswith('∃'):
        # if sub-formula starting from third symbol is enclosed, it is existential form
        if contained(formula[2:]):
            return True

        # from third symbol, look for other connectives
        for i in range(2, len(formula)-1):
            if formula[i] in ['∧', '∨', '→', '⊕', '↔']:
                left_formula = formula[:i].strip()
                right_formula = formula[i+1:].strip()
                if is_formula(left_formula) and is_formula(right_formula):
                    return False
        return True
    return False
# is_existential


# determine if a formula is universal
def is_forall(formula):
    if not '∀' in formula:
        return False
    formula = "".join(formula.split())
    if formula.startswith('(∀x)') or formula.startswith('(∃x)'):
        formula = formula[1:3] + formula[4:]
    if contained(formula):
        formula = formula[1:-1]
    if not is_balanced_parentheses(formula):
        return False

    if formula.startswith('∀'):
        # if sub-formula starting from third symbol is enclosed, it is universal form
        if contained(formula[2:]):
            return True

        # from third symbol, look for other connectives
        for i in range(2, len(formula)-1):
            if formula[i] in ['∧', '∨', '→', '⊕', '↔']:
                left_formula = formula[:i].strip()
                right_formula = formula[i+1:].strip()
                if is_formula(left_formula) and is_formula(right_formula):
                    return False
        return True
    return False
# is_forall(formula)


# determine the form of a formula
def quelle(formula):
    if contained(formula):
        formula = formula[1:-1]

    if is_predicate(formula):
        return f"{formula} is a Predciate"
    elif is_negation(formula):
        return f"{formula} is a Negation"
    elif is_equi(formula):
        return f"{formula} is a Equiv"
    elif is_implies(formula):
        return f"{formula} is a Implies"
    elif is_conjunction(formula):
        return f"{formula} is a Conjunction"
    elif is_disjunction(formula):
        return f"{formula} is a Disjunction"
    elif is_xor(formula):
        return f"{formula} is a Xor"
    elif is_existential(formula):
        return f"{formula} is a Existential"
    elif is_forall(formula):
        return f"{formula} is a Forall"
    return "Not-a-formula"
# quelle(formula)


if __name__ == "__main__":
    pass
