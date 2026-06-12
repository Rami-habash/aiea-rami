# runner.py
# controlled experimenting
import os, json, glob, time, shutil
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# stamping runs to keep track
RUN_STAMP = time.strftime("%Y-%m-%d-%H%M%S")

import run_cot
import run_standard
import run_symbol
import run_errfix
from config.Settings import config

#============ Config ============#
# folio samples and workers
# max follio is 182 samples
N_SAMPLES = 182
NUM_WORKERS = 182
NUM_PROCESSES = NUM_WORKERS # changed the process pool to a thread pool

# which pipeline to test
RUN_COT = True
RUN_STANDARD = True 
RUN_LTRAG = True 
LTRAG_COT = True # yes or no to cot in LTRAG

# models
MODELS = ["gpt-5.4-mini"]

# for 4o
EFFORTS = ["low"]

# (uncached_in, cached_in, out) prices
# gpt-5.4-nano: https://developers.openai.com/api/docs/models/compare ; gpt-4o: standard OpenAI pricing.
PRICE_TABLE = {
    "gpt-5.4-nano": (0.20, 0.02, 1.25),
    "gpt-5.4-mini": (0.75, 0.08, 4.5),
    "gpt-4o": (5, 0, 15.00),
    "gpt-4o-mini": (0.15, 0.08, 0.6),
    "gpt-3.5-turbo": (0.5, 0, 1.5),
    "gpt-4.1-mini": (0.4, 0.1, 1.6)
}

#================================#

def set_model(model, effort):
    for role in ("extra", "symbol", "cot", "standard", "errfix"):
        config["agent"][role]["model"] = model
        if role != "extra":
            config["agent"][role]["reasoning_effort"] = effort
    # route output saving to the model chosen HERE in the runner — the run_*.py modules bind
    # output_dir at import to config's default, so push the live model's dir into them
    mn = model.split("/")[-1] if "/" in model else model
    out_dir = f"./data.nosync/{config['task']}/{mn}"
    os.makedirs(out_dir, exist_ok=True)
    for mod in (run_cot, run_standard, run_symbol, run_errfix):
        mod.output_dir = out_dir
    run_errfix.sym_model_name = mn

# all modes in pipeline
# LTRAG = symbol + errfix
PIPELINE_PATTERNS = {"COT": ["*{s}_cot.jsonl"], "STANDARD": ["*{s}_standard.jsonl"],
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

def compute_price(tin, tcached, tout, treason, model):
    # handles from price table
    pin, pcached, pout = PRICE_TABLE.get(model, PRICE_TABLE["gpt-5.4-nano"])
    uncached = tin - tcached
    return (uncached*pin + tcached*pcached + tout*pout) / 1e6

def print_results(model=None, effort=None):
    # model start
    output_dir = run_cot.output_dir
    print("\n" + "="*60)
    print(f"{'PIPELINE':<12} {'ID':<6} {'TRUTH':<10} {'PRED':<10} {'CORRECT'}")
    print("="*60)
    totals = {}

    # results for esch mode
    s = f"_{effort or 'na'}"
    # ltrag pulls from fully fixed file
    for pattern, label in [(f"*{s}_cot.jsonl", "COT"), (f"*{s}_standard.jsonl", "STANDARD"),
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
    if model is not None:
        print(f"\nTOKENS [{model} / {effort or 'none'}]")
        grand = [0, 0, 0, 0]
        for label, t in compute_tokens(effort).items():
            print(f"  {label:<10}  in={t[0]:>7,}  cached={t[1]:>7,}  out={t[2]:>7,}  reasoning={t[3]:>7,}  cost=${compute_price(*t, model):.4f}")
            grand = [g + x for g, x in zip(grand, t)]
        print(f"  {'TOTAL':<10}  in={grand[0]:>7,}  cached={grand[1]:>7,}  out={grand[2]:>7,}  reasoning={grand[3]:>7,}  cost=${compute_price(*grand, model):.4f}")
    print("="*60 + "\n")

# run processes
# number of samples and processes tested
def main(n_samples, n_processes):
    if RUN_COT:
        run_cot.run_parallel(num_lines=n_samples, num_processes=n_processes)

    if RUN_STANDARD:
        run_standard.run_parallel(num_lines=n_samples, num_processes=n_processes)

    if RUN_LTRAG:
        config["agent"]["symbol"]["cot"] = LTRAG_COT
        config["agent"]["errfix"]["cot"] = LTRAG_COT
        run_symbol.run_parallel(num_lines=n_samples, num_processes=n_processes)
        run_errfix.run_parallel(num_lines=n_samples, num_processes=n_processes)

if __name__ == "__main__":
    runs = []
    for model in MODELS:
        for effort in EFFORTS:
            print(f"\n{'#'*60}\n# mode={model} effort={effort}\n{'#'*60}")
            set_model(model, effort)
            main(N_SAMPLES, NUM_PROCESSES)

            # archive a dated copy of this run
            arch = f"./runs_archive/{model.split('/')[-1]}/{RUN_STAMP}"
            os.makedirs(arch, exist_ok=True)
            for f in glob.glob(f"{run_cot.output_dir}/*_{effort or 'na'}*.jsonl"):
                shutil.copy2(f, arch)

            runs.append((model, effort))

    for model, effort in runs:
        print(f"\n{'#'*60}\n# RESULTS model={model} effort={effort}\n{'#'*60}")
        print_results(model, effort)

