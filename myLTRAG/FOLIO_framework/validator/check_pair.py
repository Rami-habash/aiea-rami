import re
from z3 import *
from auxiliary import *
from translate import *

# check if any predicate was translated as constant or constant as predicate
def check_p2c_c2p(predicates_dict1, constants_set1, predicates_dict2, constants_set2):
    pr1_in_con2 = [key for key in predicates_dict1 if key in constants_set2]
    con1_in_pr2 = [item for item in constants_set1 if item in predicates_dict2]

    if not pr1_in_con2 and not con1_in_pr2:
        return True, ""
    elif not pr1_in_con2:
        return False, "C2P"
    elif not con1_in_pr2:
        return False, "P2C"
    else:
        return False, "P2C && C2P"
# check_p2c_c2p(predicates_dict1, constants_set1, predicates_dict2, constants_set2)


# create function for each predicate symbol
def create_functions(predicates_dict):
    functions = {}

    for name, arity in predicates_dict.items():
        sorts = [IntSort() for _ in range(arity)]
        sorts.append(BoolSort())
        globals()[name] = Function(name, *sorts)

    return functions
# create_functions(predicates_dict)


# check equivalence
def check_equivalence(z3_formula1, z3_formula2, predicates_set):
    # try:
        # Create a Z3 solver instance
        solver = Solver()

        x = Int('x')
        y = Int('y')
        z = Int('z')
        t = Int('t')
        w = Int('w')
        v = Int('v')

        # create predicate function set
        create_functions(predicates_set)

        # Assert the equivalence of the translated formulas
        solver.add(Not(eval(z3_formula1) == eval(z3_formula2)))
        result = solver.check()
        return result == unsat
# check_equivalence(z3_formula1, z3_formula2, predicates_set)


# preprocessing
def preproccess(formula):
    exceptions = []
    # remove excess prefixes
    # region
    if formula.startswith("- ") or (formula[0].isdigit() and formula[1] == '.'):
        exceptions.append("PrefixListSymbol")
        if formula.startswith("- "):
            formula = formula[2:]
        elif formula[0].isdigit() and formula[1] == '.':
            formula = formula[2:]
    # endregion

    # error logic symbols
    # region
    wrong_symbols = [' v ', '->', '^']
    correct_symbols = ['∨', '→', '⊕']
    for i in range(len(wrong_symbols)):
        if wrong_symbols[i] in formula:
            formula = formula.replace(wrong_symbols[i], correct_symbols[i])
            exceptions.append("WrongSymbol")
    if '→ ∨' in formula:
        exceptions.append("AdjacentConnective")
    # endregion

    # quantifier not translated
    # region
    if 'forall ' in formula or 'for all ' in formula or 'All ' in formula or \
        'Forall ' in formula or 'All(x)' in formula:
        exceptions.append("No2Quantifier")
        all_strings = ['forall ', 'for all ', 'All ', 'Forall ']
        for all_str in all_strings:
            formula = formula.replace(all_str, '∀')
        formula = formula.replace('All(x)', '∀x')
    if 'Exist ' in formula:
        exceptions.append("No2Quantifier")
        exist_strings = ['Exist ']
        for exist_str in exist_strings:
            formula = formula.replace(exist_str, '∃')
    if 'No ' in formula or 'No(' in formula:
        exceptions.append("Weird-NO")
    if "∀x," in formula:
        formula = formula.replace("∀x,y,z", "∀x∀y∀z")
        formula = formula.replace("∀x,y", "∀x∀y")
        exceptions.append("un-Q")
    get_rid_of_paren = ['(∀x)', '(∃x)']
    for string in get_rid_of_paren:
        formula = formula.replace(string, string[1:-1])
    # endregion

    # other symbols
    # region
    other_symbols = ['⇏', '=', '>', '<', '.', '⊆', '~', '()', ':', '∈', '+', '≥', '≤']
    for other in other_symbols:
        if other in formula:
            exceptions.append("OtherSymbol")
            break
    # endregion

    # lowercase predicates: 24::contains, 28::..., 43::hasClass..., 78::selEel, 92::anti, 217::iPhone
        # 552::boapay, canBe, canTrans, 638::latent..., 675::pscamera
    # region
    lower_predicates = ['contains(', 'highIncome(', 'takeBus(', 'drive(', 'haveCars(', \
                        'student(', 'worksAtMeta(', 'hasClassDuringWeekend(', 'seaEel(', \
                        'anti-abortion(', 'iPhone', 'boapaymentcards(', 'canBeUsedWith(', \
                        'canTransferTo(', 'latentDirichletAllo', 'pscamera']
    upper_predicates = ['Contains(', 'HighIncome(', 'TakeBus(', 'Drive(', 'HaveCars(', \
                        'Student(', 'WorksAtMeta(', 'HasClassDuringWeekend(', 'SeaEel(', \
                        'Anti-abortion(', 'IPhone', 'Boapaymentcards(', 'CanBeUsedWith(', \
                        'CanTransferTo(', 'LatentDirichletAllo', 'Pscamera']
    for lu in range(len(lower_predicates)):
        if lower_predicates[lu] in formula:
            formula = formula.replace(lower_predicates[lu], upper_predicates[lu])
            exceptions.append("WrongPredicate")

    if '12HourWorkHours(' in formula:
        exceptions.append("PreStartswithNum")
    # endregion

    # error parentheses
    # region
    if '[' in formula:
        formula = formula.replace('[', '(')
        formula = formula.replace(']', ')')
        exceptions.append("WrongParen")
    if not is_balanced_parentheses(formula) or formula.count('(') == 0:
        exceptions.append("UnMatchParen")
    if '`' in formula:
        formula = formula.replace('`', '')
    # endregion

    return formula, exceptions


# query equivalence
def query(formula1, formula2):
    if len(formula2) == 0:
        return "Empty"

    # preprocess formula2
    formula2, exceptions = preproccess(formula2)

    # extract predicate and constant, check for misuse
    predicates_dict1, constants_set1 = extract_predicates_and_constants(formula1)
    predicates_dict2, constants_set2 = extract_predicates_and_constants(formula2)
    wrong_use, info = check_p2c_c2p(predicates_dict1, constants_set1, predicates_dict2, constants_set2)
    if not wrong_use:
        return info
    elif '_' in constants_set2:
        return "_AsVar"
    else:
        # if there are predicates with different elements, error; otherwise merge predicate sets
        for key, value in predicates_dict2.items():
            if key in predicates_dict1:
                if predicates_dict1[key] != value:
                    return "P-With-Different-Array"
            else:
                    predicates_dict1[key] = value

        # directly stop in other cases
        # region
        if "OtherSymbol" in exceptions:
            return "OtherSymbol"
        if "Weird-NO" in exceptions:
            return "Weird-NO"
        if "UnMatchParen" in exceptions:
            return "UnMatchParen"
        if "AdjacentConnective" in exceptions:
            return "AdjacentConnective"
        if "PreStartswithNum" in exceptions:
            return "PreStartswithNum"
        if "Empty" in exceptions:
            return "Empty"
        # endregion

        # start attempting analysis here
        z3_formula1 = replace_const(translate(formula1))
        z3_formula2 = replace_const(translate(formula2))
        if "-----InputError-----" in z3_formula1 or "." in z3_formula1:
            return "Dataset"

        # invalid statement, check during batch processing
        # region
        print("z3_formula1 = " + z3_formula1)
        print("z3_formula2 = " + z3_formula2)
        # endregion

        result = check_equivalence(z3_formula1, z3_formula2, predicates_dict1)
        if  result is True:
            return "Equivalent", exceptions
        else:
            return "Not-Equivalent", exceptions
# query(formula1, formula2)
