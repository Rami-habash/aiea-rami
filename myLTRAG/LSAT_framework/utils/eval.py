import re
from utils.sat_problem_solver import LSAT_Z3_Program


# check for initial format errors
def check_exp(logic_program):
    # split the logic program into different parts
    lines = [x for x in logic_program.splitlines() if not x.strip() == ""]

    decleration_start_index = lines.index("# Declarations")
    constraint_start_index = lines.index("# Constraints")
    option_start_index = lines.index("# Options")

    declaration_statements = lines[decleration_start_index + 1:constraint_start_index]
    constraint_statements = lines[constraint_start_index + 1:option_start_index]
    option_statements = lines[option_start_index + 1:]

    err_msg = "\n# Grammer Check\nHere are the results of the grammar check. Please make the necessary corrections for the following cases and revise any other potential grammar issues based on the actual situation.\n\n"
    # record auxiliary info length
    start_len = len(err_msg)

    index = 1

    # declaration section errors, mainly variable exception symbols.
    for statement in declaration_statements:
        if "'" in statement or "#" in statement:
            err_msg += f"{index}. The declaration section contains following marks [\"'\", \"#\"] in variables, which may cause difficulties in parsing the entire program.\n"
            index += 1
            break

    # the following sections mainly detect exception symbols
    exception_symbols = {'->', '|', '?'}
    parentheses_check = True
    for statement in constraint_statements:
        for symbol in exception_symbols:
            contains = []
            if symbol in statement:
                contains.append(symbol)
                err_msg += f"{index}. The constraint statement `{statement}` has an exception symbol `{contains}`, please modify this sentence. \n"
                index += 1

        _, lc, rc = is_balanced_parentheses(statement)
        if lc < rc and parentheses_check:
            err_msg += f"{index}. The Constraints part seems to have the issue of formulas not being written on a single line.\n"
            index += 1
            parentheses_check = False

    parentheses_check = True
    for statement in option_statements:
        for symbol in exception_symbols:
            contains = []
            if symbol in statement:
                contains.append(symbol)
                err_msg += f"{index}. The option statement `{statement}` has an exception symbol `{contains}`, please modify this sentence.\n"
                index += 1
        _, lc, rc = is_balanced_parentheses(statement)
        if lc < rc and parentheses_check:
            err_msg += f"{index}. The Options part seems to have the issue of formulas not being written on a single line.\n"
            index += 1
            parentheses_check = False

    # if no error info has been added, set error info to empty
    if len(err_msg) == start_len:
        err_msg = ""

    return err_msg, index


# process parseable logic programs
def check_output(output: list, index: int, others: str):
    log = ""
    types_record = []

    # count already selected options
    geted_options = 0
    for item in output:
        if len(item) < 4:
            geted_options += 1

    # record classic error types
    error_types = {
        "not defined": "This error indicates that there seem to be some function or variable names that you have not declared in the declaration area.",
        "not supported": "It is not supported to perform undefined operations on certain quantities.",
        "unsupported operand": "It is not supported to perform undefined operations on certain quantities.",
        "Symbolic expressions": "It is not supported to perform undefined operations on certain quantities.",
        "Sort mismatch": "Check the usage of each function, including the domain and range. For example, if the parameter of function A is of type T1, performing the operation A(T2) (which is incorrect) on type T2. Of course, this includes whether there are conflicts in the return types, etc. Another possibility is that, it seems that there is a mapping error when using certain functions, for example, function A was originally defined with a range of languages, but a situation like \"A(x) = China\" occurred.",
        "If() missing": "The If() function was used incorrectly; perhaps using Implies() would be more appropriate.",
        "Z3 sort expected": "Check whether there are comments in the `# Declarations` section, which is prohibited.",
    }

    if len(output) > 4:
        output = output[4:]
    elif len(output) == 4:
        output = []
        # this case is when program runs normally but no option is selected, i.e., empty selection
        log += f"{index}. No correct option problem. All options in this program are judged as incorrect, but this question is a single-choice question. It seems that some information has been overlooked, and the program needs to be re-examined.\n"
        index += 1
        types_record.append("choice question")
    for error in output:
        # if a choice has already been made, skip error checking
        if geted_options != 0:
            if geted_options > 1:
                log += f"{index}. Multiple-choice question. This program has multiple options (`{output}`) judged as correct, but this question is a single-choice question. It seems that some information has been overlooked, and the program needs to be re-examined.\n"
                index += 1
                types_record.append("choice question")
            break

        unrecorded = True
        for et_head, et_tail in error_types.items():
            if et_head.lower() in error.lower():
                log += f"{index}. {error}\n\t{et_tail}\n"
                index += 1
                unrecorded = False
                types_record.append(et_head)
                break
        if unrecorded and len(error) > 4:
            others += error + "\n"

    if log:
        log = "\n# Program Error\nThis section will provide you with the program error encountered during the solving process after the logical program has been parsed.\n" + log

    return log, types_record, others


# get solve program error and initial syntax error check
def get_exception(logic_program, id):
    print("Checking for syntax problems...\n")
    """
        Errors are divided into three categories:
        - First: uses check_exp to check exception symbols; recorded as grammar.
        - Second: uses check_output to check errors encountered after parse run; recorded as program.
        - Third: not encountered during parsing, captured in the except block below; recorded as parsing.
    """
    grammar_e, index = check_exp(logic_program)    # check format exceptions in each part

    parsing_e = ""    # record exceptions during solving process
    others = ""
    emsg = ""
    output = []
    try:
        z3_program = LSAT_Z3_Program(logic_program, 'AR-LSAT', id)
        output, emsg = z3_program.execute_program()
        if output == None:
            output = []
    except Exception as e:
        error_message = str(e)
        parsing_e = "\n# Parsing Failed\nWhen encountering such an error message, it indicates that the preceding logical program is unresolvable.\n"
        if "'cache_dir'" in error_message:
            parsing_e += f"{index}. The logic program does not strictly follow the grammatical rules; for example: \n1. it is not divided into three parts: \"Declarations\", \"Constraints\", and \"Options\".\n2. Or there is statement is split into multiple lines.\nYou may need to regenerate the program.\n"
            index += 1
        elif "TimeoutError".lower() in error_message:
            parsing_e += f"{index}. TimeoutError. Some options were poorly translated, which led the solving process into an infinite loop. Check the translation of the options."
            index += 1
        else:
            others += error_message + "\n"

    program_e, errortypes, others = check_output(output, index, others)

    if "SyntaxError: invalid syntax" in emsg:
        parsing_e += f"{index}. `SyntaxError: invalid syntax`. There might be some syntax errors."
        emsg = emsg.replace("SyntaxError: invalid syntax", "")
        errortypes.append("SyntaxError: invalid syntax")
        index += 1

    # with the below checks, if no error info, ensure return empty
    msg = f"{grammar_e}\n{program_e}\n{parsing_e}"
    if re.fullmatch(r'[\n\r]*', msg):
        msg = ""

    if emsg:
        others += f"\n{emsg}"
    if re.fullmatch(r'[\n\r]*', others):
        others = ""
    else:
        others = f"\n\n\n***error***:\n{others}"

    if others:
        print(f"\tthis syntax check omitted error:\n\t\t{others}")
    print("syntax check complete...\n")
    return msg, errortypes, others


def is_balanced_parentheses(formula):
    stack = []
    left_count = 0  # counter for left parentheses
    right_count = 0  # counter for right parentheses
    for i, char in enumerate(formula):
        if char == "(":
            stack.append(("left", i))
            left_count += 1
        elif char == ")":
            right_count += 1
            if stack and stack[-1][0] == "left":
                stack.pop()
            else:
                stack.append(("right", i))
    return stack, left_count, right_count


if __name__ == "__main__":
    pass
