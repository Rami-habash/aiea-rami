# myUtils.py
# Prover9 setup and FOL evaluation utilities
# Many functions identical to LINC's eval/tasks/utils.py
import os
import re
from nltk.sem import Expression
from nltk.inference.prover9 import Prover9

PROVER9_PATH = "/opt/homebrew/bin/prover9"
os.environ["PATH"] = os.path.dirname(PROVER9_PATH) + ":" + os.environ.get("PATH", "")

read_expr = Expression.fromstring
prover = Prover9(timeout=10)

# safety nets for nltk fol syntax
#------------#
def get_all_variables(text: str) -> list[str]:
    # from LINC's get_all_variables() in eval/tasks/utils.py
    pattern = r'\([^()]+\)'
    matches = re.findall(pattern, text)
    all_variables = []
    for m in matches:
        m = m[1:-1]
        m = m.split(",")
        all_variables += [i.strip() for i in m]
    return list(set(all_variables))

def reformat_fol(fol):
    # from LINC's reformat_fol() in eval/tasks/utils.py
    translation_map = {
        "0": "Zero", 
        "1": "One",
        "2": "Two",
        "3": "Three",
        "4": "Four",
        "5": "Five",
        "6": "Six",
        "7": "Seven",
        "8": "Eight",
        "9": "Nine",
        ".": "Dot",
        "’": "",
        "-": "_",
        "'": "",
        " ": "_"
    }
    all_variables = get_all_variables(fol)
    for variable in all_variables:
        variable_new = variable[:]
        for k, v in translation_map.items():
            variable_new = variable_new.replace(k, v)
        fol = fol.replace(variable, variable_new)
    return fol
#--------------#

def Prover9_check(goal_expr, prem_exprs) -> tuple:
    # nltk wrapper: _call_prover9() gives us the raw stdout which has 
    # the proof section of how it got to the conclusion. 
    inp = prover.prover9_input(goal_expr, prem_exprs)
    stdout, stderr = prover._call_prover9(inp)
    if "PROOF" in stdout:
        start = stdout.index("============================== PROOF")
        end = stdout.index("============================== end of proof", start)
        return True, stdout[start:end + len("============================== end of proof")]
    # not proved
    return False, ""


def evaluate_fol(assumptions: list[str], goal: str) -> dict:
    # from LINC's eval/tasks/utils.py evaluate()
    try:
        assumptions_nltk = [reformat_fol(a) for a in assumptions]
        goal_nltk = reformat_fol(goal)
        prem_exprs = [read_expr(a) for a in assumptions_nltk]

        # try to prove the goal
        goal_expr = read_expr(goal_nltk)
        proved, proof = Prover9_check(goal_expr, prem_exprs)
        if proved:
            return {"verdict": "True", "proof": proof}

        # try to prove the negation
        neg_goal_expr = read_expr(f"-({goal_nltk})")
        proved, proof = Prover9_check(neg_goal_expr, prem_exprs)
        if proved:
            return {"verdict": "False", "proof": proof}

        return {"verdict": "Uncertain", "proof": ""}
    except Exception as e:
        return {"verdict": "Error", "error": str(e)}
    
"""
Self notes for potetnial future expansions:

- convert_to_nltk_rep in linc might be better to use
for folio examples.
"""