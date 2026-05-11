import re

# extract and replace constants in formula; since two formulas share predicates and constants, record constants_dict
constants_dict = {}  # stores constants that have appeared and their index
next_index = 1  # next available index
times = 0
def replace_const(z3_formula):
    global next_index
    global times
    if times == 2:
        next_index = 1
        constants_dict.clear()
        times = 0

    z3_formula = "".join(z3_formula.split())
    pattern = r'\([^()]+?\)'    # match smallest parentheses with no nested parentheses inside

    # match all possible constants in string
    arrays_set = re.findall(pattern, z3_formula)
    for arrays in arrays_set:
        arrays_modified = arrays
        constants = arrays[1:-1].split(",")
        for constant in constants:
            if constant not in ['x', 'y', 'z', 't', 'w', 'v']:
                # if constant already in dictionary, use its index; otherwise assign a new index
                if constant.lower().replace(" ", "") in constants_dict:
                    index = constants_dict[constant.lower()]
                else:
                    constants_dict[constant.lower().replace(" ", "")] = next_index
                    index = next_index
                    next_index += 1
                arrays_modified = arrays_modified.replace(constant, str(index))
                # replace constant in formula with index
        z3_formula = z3_formula.replace(arrays, arrays_modified)
    times += 1
    return z3_formula
# extra_const


# extract predicate set and constants from a formula
def extract_predicates_and_constants(formula):
    # use regex to match predicate name and its arity
    # regex pattern explanation:
    # \w+ matches one or more letter/digit characters (predicate name)
    # \((.*?)\) matches content inside parentheses, content may contain any characters, uses non-greedy match
    formula = "".join(formula.split())
    pattern = r'([A-Z][\w-]*)\((.*?)\)'
    matches = re.findall(pattern, formula)

    predicates_dict = {}
    constants_set = set()
    for match in matches:
        predicate_name = match[0]  # extract predicate name
        variables = match[1].split(',')  # extract variables inside parentheses, split by comma
        arity = len(variables)  # count variables, which is the arity

        # check if variable is a constant
        for var in variables:
            if var.strip() not in ['x', 'y', 'z', 't', 'w', 'v']:
                constants_set.add(var.strip())
        predicates_dict[predicate_name] = arity

    return predicates_dict, list(constants_set)
# extract_predicates_and_constants(formula)


# determine if a formula is enclosed by parentheses
def contained(formula):
    if len(formula) > 0 and formula[0] == '(' and formula[-1] == ')':
        cnt = 1
        for i in range(1, len(formula)-1):
            if formula[i] == '(':
                cnt += 1
            elif formula[i] == ')':
                cnt -= 1
            if cnt == 0:
                return False
        return True
    return False
# contained(formula)


# check if parentheses in formula are balanced
def is_balanced_parentheses(formula):
    # initialize left and right parenthesis counters
    left_count = 0
    right_count = 0

    # traverse each character in the expression
    for char in formula:
        # count left and right parentheses
        if char == '(':
            left_count += 1
        elif char == ')':
            right_count += 1

        # if right parenthesis count exceeds left, parentheses are unbalanced
        if right_count > left_count:
            return False

    # finally check if total left and right parenthesis counts are equal
    return left_count == right_count
# is_balanced_parentheses(formula)
