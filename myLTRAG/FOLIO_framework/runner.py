# runner.py
# controlled experimenting
import os, json, glob
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import run_cot
import run_standard
import run_symbol
import run_errfix
from config.Settings import config

#============ Config ============#
# folio samples and workers
N_SAMPLES = 182
NUM_PROCESSES = 11

# which pipeline to test
RUN_COT = True
RUN_STANDARD = True 
RUN_LTRAG = True 

# models
MODELS = ["gpt-5.4-mini"]
EFFORTS = ["none", "medium"]


# gpt-5.4-nano: from https://developers.openai.com/api/docs/models/compare
PRICE_IN = 0.20
PRICE_CACHED = 0.02
PRICE_OUT = 1.25 # same for reasoning tokens

#================================#

def set_model(model, effort):
    for role in ("extra", "symbol", "cot", "standard", "errfix"):
        config["agent"][role]["model"] = model
        if role != "extra":
            config["agent"][role]["reasoning_effort"] = effort

# all modes in pipeline
# NOTE: COT/STANDARD are swapped because of noticed bug.
# LTRAG = symbol + errfix 
PIPELINE_PATTERNS = {"COT": ["*{s}_standard.jsonl"], "STANDARD": ["*{s}_cot.jsonl"],
                     "LTRAG": ["*{s}_symbol.jsonl", "*errfix*{s}.jsonl"]}

# sum tokens by going thru json outputs of each mode
def compute_tokens(effort):
    output_dir = run_cot.output_dir
    s = f"_{effort or 'na'}"
    out = {}
    for label, pats in PIPELINE_PATTERNS.items():
        tin = tcached = tout = treason = 0
        for pat in pats:
            for path in glob.glob(os.path.join(output_dir, pat.format(s=s))):
                for line in open(path):
                    u = json.loads(line).get("usage") or {}
                    tin += u.get("in", 0)
                    tcached += u.get("cached", 0)
                    tout += u.get("out", 0)
                    treason += u.get("reasoning", 0)
        out[label] = (tin, tcached, tout, treason)
    return out

def compute_price(tin, tcached, tout, treason):
    uncached = tin - tcached
    return (uncached*PRICE_IN + tcached*PRICE_CACHED + tout*PRICE_OUT) / 1e6

def print_results(model=None, effort=None):
    # model start
    output_dir = run_cot.output_dir
    print("\n" + "="*60)
    print(f"{'PIPELINE':<12} {'ID':<6} {'TRUTH':<10} {'PRED':<10} {'CORRECT'}")
    print("="*60)
    totals = {}

    # results for esch mode
    s = f"_{effort or 'na'}"
    # COT/standard swapped again and ltrag pulls from fully fixed file
    for pattern, label in [(f"*{s}_standard.jsonl", "COT"), (f"*{s}_cot.jsonl", "STANDARD"),
                            (f"*{s}_full_errfix_*.jsonl", "LTRAG")]:
        files = glob.glob(os.path.join(output_dir, pattern))
        if not files:
            continue
        correct = total = 0
        for line in open(sorted(files)[-1]):
            d = json.loads(line)
            c = d.get("same", False)
            correct += c
            total += 1
            print(f"{label:<12} {d['id']:<6} {d['label']:<10} {d.get('label-AI','?'):<10} {'✓' if c else '✗'}")
        totals[label] = (correct, total)
    print("="*60)
    for name, (c, t) in totals.items():
        print(f"{name:<12} {c}/{t} ({c/t:.1%})")
    
    # printing out tokens for each mode
    if effort is not None:
        print(f"\nTOKENS [{model} / {effort}]")
        grand = [0, 0, 0, 0]
        for label, t in compute_tokens(effort).items():
            print(f"  {label:<10}  in={t[0]:>7,}  cached={t[1]:>7,}  out={t[2]:>7,}  reasoning={t[3]:>7,}  cost=${compute_price(*t):.4f}")
            grand = [g + x for g, x in zip(grand, t)]
        print(f"  {'TOTAL':<10}  in={grand[0]:>7,}  cached={grand[1]:>7,}  out={grand[2]:>7,}  reasoning={grand[3]:>7,}  cost=${compute_price(*grand):.4f}")
    print("="*60 + "\n")

# run processes

# number of samples and processes tested
def main(n_samples, n_processes):
    if RUN_COT:
        run_cot.run_parallel(num_lines=n_samples, num_processes=n_processes)

    if RUN_STANDARD:
        run_standard.run_parallel(num_lines=n_samples, num_processes=n_processes)

    if RUN_LTRAG:
        run_symbol.run_parallel(num_lines=n_samples, num_processes=n_processes)
        run_errfix.run_parallel(num_lines=n_samples, num_processes=n_processes)

if __name__ == "__main__":
    runs = []
    for model in MODELS:
        for effort in EFFORTS:
            print(f"\n{'#'*60}\n# mode={model} effort={effort}\n{'#'*60}")
            set_model(model, effort)
            main(N_SAMPLES, NUM_PROCESSES)
            runs.append((model, effort))

    for model, effort in runs:
        print(f"\n{'#'*60}\n# RESULTS model={model} effort={effort}\n{'#'*60}")
        print_results(model, effort)

