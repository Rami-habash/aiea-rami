# myUtils.py
# Prover9 setup and FOL evaluation utilities
# Some functions similar to LINC's eval/tasks/utils.py
import os
import re
from nltk.sem import Expression
from nltk.inference.prover9 import Prover9Command, Prover9

PROVER9_PATH = "/opt/homebrew/bin/prover9"
os.environ["PATH"] = os.path.dirname(PROVER9_PATH) + ":" + os.environ.get("PATH", "")

read_expr = Expression.fromstring
prover = Prover9(timeout=10)


def convert_to_nltk_rep(logic_formula: str) -> str:
    # similar to LINC's eval/tasks/utils.py convert_to_nltk_rep()
    # this is a simplified version for NLTK
    _NLTK_KEYWORDS = {'all', 'exists', 'some', 'and', 'not', 'or', 'if', 'iff'}
    constant_pattern = r'\b([a-z]{2,})(?!\()'
    logic_formula = re.sub(
        constant_pattern,
        lambda m: m.group(1) if m.group(1) in _NLTK_KEYWORDS else m.group(1).capitalize(),
        logic_formula
    )
    quant_pattern = r"(all\s|exists\s)([a-zA-Z])(?!\.)"
    logic_formula = re.sub(quant_pattern, lambda m: m.group(1) + m.group(2) + ".", logic_formula)
    return logic_formula


def get_proof_trace(goal_expr, prem_exprs):
    # use nltk's prover9 wrapper to get the raw proof output
    # _call_prover9() gives us the raw stdout which has the proof section
    # of how it got to the conclusion. 
    inp = prover.prover9_input(goal_expr, prem_exprs)
    stdout, stderr = prover._call_prover9(inp)
    if "PROOF" in stdout:
        start = stdout.index("============================== PROOF")
        end = stdout.index("============================== end of proof", start)
        return stdout[start:end + len("============================== end of proof")]
    return ""


def evaluate_fol(assumptions: list[str], goal: str) -> dict:
    # similar to LINC's eval/tasks/utils.py evaluate()
    # my version robustifies error handling to adapt to
    # my prompt based parsing
    try:
        assumptions_nltk = [convert_to_nltk_rep(a) for a in assumptions]
        goal_nltk = convert_to_nltk_rep(goal)
        prem_exprs = [read_expr(a) for a in assumptions_nltk]

        # try to prove the goal
        goal_expr = read_expr(goal_nltk)
        cmd = Prover9Command(goal_expr, prem_exprs, timeout=10)
        if cmd.prove():
            proof = get_proof_trace(goal_expr, prem_exprs)
            return {"verdict": "True", "proof": proof}

        # try to prove the negation
        neg_goal_expr = read_expr(f"-({goal_nltk})")
        neg_cmd = Prover9Command(neg_goal_expr, prem_exprs, timeout=10)
        if neg_cmd.prove():
            proof = get_proof_trace(neg_goal_expr, prem_exprs)
            return {"verdict": "False", "proof": proof}

        return {"verdict": "Uncertain", "proof": ""}
    except Exception as e:
        return {"verdict": "Error", "error": str(e)}