from z3 import *
import re
from .translate import *
# set_param("sat.euf", True)
# set_param("tactic.default_tactic", "sat")
# set_param("solver.proof.log", "proof_log.smt2")

# extract and replace constants in formula; since the same group of premises share constants, record constants_dict
# region
constants_dict = {}  # stores constants that have appeared and their index
next_index = 1  # next available index
def dict_clear():
    global next_index
    next_index = 1
    constants_dict.clear()

def replace_const(z3_formula):
    global next_index

    z3_formula = "".join(z3_formula.split())
    pattern = r'\([^()]+?\)'    # match smallest parentheses with no nested parentheses inside

    # match all possible constants in string
    arrays_set = re.findall(pattern, z3_formula)
    for arrays in arrays_set:
        arrays_modified = arrays
        constantss = arrays[1:-1].split(",")
        constantss.sort(key=len, reverse=True)
        for constant in constantss:
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
    return z3_formula
# endregion
# replace_const(z3_formula)


# extract predicate set from a formula
# region
predicates_dict = {}
def predicates_clear():
    predicates_dict.clear()
def extract_predicates(formula):
    # use regex to match predicate name and its arity
    # regex pattern explanation:
    # \w+ matches one or more letter/digit characters (predicate name)
    # \((.*?)\) matches content inside parentheses, content may contain any characters, uses non-greedy match
    formula = "".join(formula.split())
    pattern = r'([A-Z][\w-]*)\((.*?)\)'
    matches = re.findall(pattern, formula)

    for match in matches:
        predicate_name = match[0]  # extract predicate name
        variables = match[1].split(',')  # extract variables inside parentheses, split by comma
        arity = len(variables)  # count variables, which is the arity

        predicates_dict[predicate_name] = arity

    return predicates_dict
# endregion
# extract_predicates(formula)


# translate response to z3-compatible form
def translate_premises(response):
    premises = []
    i = 1
    for premise in response:
        premise = premise.replace('.', '')
        premises.append(translate(premise))

    return premises
# translate_premises(response)


# for each predicate symbol and constant, create function
def create_functions(predicates_dict):
    for name, arity in predicates_dict.items():
        sorts = [IntSort() for _ in range(arity)]
        sorts.append(BoolSort())
        globals()[name] = Function(name.lower(), *sorts)
# perform reasoning on the whole example
def reason(premises, conclusion, predicates_dict,origin_premises,origin_conclusion):
    try:
        # create a solver
        solver = Solver()
        # output solving process
        # set_param("solver.proof.check", False)
        # onc = OnClause(solver, print)
        # solver.from_file("proof_log.smt2")
        # declare logic symbols
        create_functions(predicates_dict)

        # variable declaration area
        x = Int('x')
        y = Int('y')
        z = Int('z')
        u = Int('u')
        v = Int('v')
        w = Int('w')

        # replace constants
        dict_clear()
        premises_after_replace = []
        for premise in premises:
            new_premise = replace_const(premise)
            premises_after_replace.append(new_premise)
        conclusion = replace_const(conclusion)
        # add premises to solver
        i = 0
        for premise in premises_after_replace:
            try:
                # attempt to evaluate and add premise
                solver.add(eval(premise))
            except Exception as e:
                # if problems occur, print these premises
                return f"premise{i} {origin_premises[i]}\n{premise}\n exception: {e}"
            i+=1
        # add negation of conclusion to solver
        # print(f"conclusion= ", end="")
        # print(conclusion)
        try:
            solver.add(Not(eval(conclusion)))
        except Exception as e:
            # if problems occur, print these premises
            return f"conclusion{origin_conclusion}  {conclusion}, exception: {e}"

        # check if solution exists; if not, premises cannot derive conclusion
        if solver.check() == unsat:
            return True
        else:
            return False
    except SyntaxError as e:
        return f"SyntaxError.{e}"
    except Z3Exception as e:
        return f"Z3Exception.{e}"

def log(msg):
    # append to error.log
    with open("error.log", "a", encoding='utf-8') as f:
        f.write(msg+"\n")
    print(msg)

# wrapper function: accepts a complete example given in dictionary form, must at least contain "response" and "conclusion-AI"
def inference(premises:list,conclusion:str):
    predicates = {}
    predicates_clear()
    # replace original special symbols
    conclusion = conclusion.replace('.', '').replace('\u2019', '')
    for i in range(len(premises)):
        premises[i] = premises[i].replace('.', '').replace('\u2019', '')
        predicates = extract_predicates(premises[i])
    # extract predicates, constants
    predicates = extract_predicates(conclusion)
    premises = translate_premises(premises)
    conclusion = translate(conclusion.replace('.', ''))
    print(premises)
    print(conclusion)
    return interface_from_z3str(premises,conclusion,predicates)

def interface_from_z3str(premises:list,conclusion:str,predicates:list):
    case1 = reason(premises, conclusion, predicates, premises, conclusion)
    case2 = reason(premises, "Not("+conclusion+")", predicates, premises, conclusion)
    # if not bool type, log the error
    if not isinstance(case1, bool):
        err_msg = f"""\nnew error\nconclusion: {conclusion}\nformatted conclusion: {conclusion}\npremise: {premises}\nformatted premise: {premises}\nerror: {case1}\n"""
        # log(err_msg)
        return "Error",err_msg
    if not isinstance(case2, bool):
        err_msg = f"""\nnew error\nconclusion: {conclusion}\npremise: {premises}\nerror: {case2}\n"""
        # log(err_msg)
        return "Error",err_msg

    if case1 and not case2:
        return "True",""
    elif not case1 and case2:
        return "False",""
    else:
        return "Unknown",""
