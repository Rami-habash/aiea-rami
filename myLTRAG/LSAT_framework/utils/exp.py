"""
utility functions for processing logic formulas
"""
import re
from typing import List, Tuple


def fix_exps(logic_program):
    # complete variables for cases like [c1, c2:compositions]
    lines = [x for x in logic_program.splitlines() if not x.strip() == ""]

    decleration_start_index = lines.index("# Declarations")
    constraint_start_index = lines.index("# Constraints")
    option_start_index = lines.index("# Options")

    declaration_statements = lines[decleration_start_index + 1:constraint_start_index]
    constraint_statements = lines[constraint_start_index + 1:option_start_index]
    option_statements = lines[option_start_index + 1:]

    def complete_variables(statement):
        # define regex to match cases like [c1, c2:compositions] or [g1, g2:type]
        pattern = r'\[([a-zA-Z0-9_,\s]+):([a-zA-Z0-9]+)\]'

        # use regex to find all matching items
        def replace(match):
            # get variable part and type part inside brackets
            variables_part = match.group(1).strip()  # variable part
            type_part = match.group(2).strip()  # type part

            # split variables by comma, removing possible spaces
            variables = [var.strip() for var in variables_part.split(',')]

            # return completed string form: each variable:type
            return f"[{', '.join([f'{var}:{type_part}' for var in variables])}]"

        # use regex to replace all matching items
        completed_statement = re.sub(pattern, replace, statement)

        return completed_statement

    # repair constraint_statements and option_statements in variable
    constraint_statements = [complete_variables(statement) for statement in constraint_statements]
    option_statements = [complete_variables(statement) for statement in option_statements]


    # reassemble repaired parts back into logic_program
    new_logic_program = "\n".join(lines[:decleration_start_index + 1] + declaration_statements +
                                  ["# Constraints"] + constraint_statements +
                                  ["# Options"] + option_statements)

    return new_logic_program


if __name__ == "__main__":
    from eval import check_all_exp

    p = [
'PrivateIvyLeagueResearchUniversity(yaleUniversity)',    ]
    c = "exists e. Geen(e) -> ae(e)"
    print(check_all_exp(p,c))
