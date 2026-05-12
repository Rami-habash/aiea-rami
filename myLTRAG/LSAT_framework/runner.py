# runner.py
# controlled experimenting
import os, json, glob, subprocess
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from llm.base import DATATYPE, MODEL

# Config
N_SAMPLES = 10
NUM_PROCESSES = 6
RAG_K = 3 # for the fixer only. The actual is in config
TEMP = 0.2

RUN_COT = True
RUN_LTRAG = True 

# finding where outputs of model are saved
def _get_output_dir():
    if "/" in MODEL:
        return os.path.join("data", DATATYPE, MODEL.split("/")[-1])
    return os.path.join("data", DATATYPE, MODEL)

# prining results of model
def print_results():
    output_dir = _get_output_dir()
    width = 74
    print("\n" + "="*width)
    print(f"{'PIPELINE':<10} {'ID':<32} {'TRUTH':<8} {'PRED':<8} CORRECT")
    print("="*width)
    totals = {}
    for pattern, label in [("Standard.jsonl", "COT"), ("dev_*.jsonl", "LTRAG")]:
        files = glob.glob(os.path.join(output_dir, pattern))
        if not files:
            print(f"  [{label}] no output file found")
            continue
        correct = total = 0
        print(f"  [{label}]")
        for line in open(sorted(files)[-1]):
            d = json.loads(line)
            truth = d.get("answer", "?")
            pred  = d.get("actual_answer", "?")
            c = truth == pred
            correct += c
            total += 1
            print(f"{'':10} {d['id']:<32} {truth:<8} {pred:<8} {'✓' if c else '✗'}")
        totals[label] = (correct, total)
        print()
    print("="*width)
    for name, (c, t) in totals.items():
        print(f"  {name:<10} {c}/{t}  ({c/t:.1%})")
    print("="*width + "\n")

# run processess
if __name__ == "__main__":
    if RUN_COT:
        if N_SAMPLES is None:
            subprocess.run(["python", "run_cot.py"], check=True)
        else:
            subprocess.run(["python", "run_cot.py", "--n_samples", str(N_SAMPLES)], check=True)

    if RUN_LTRAG:
        if N_SAMPLES is None:
            subprocess.run(["python", "run_symbol.py", str(RAG_K), str(TEMP)], check=True)
        else:
            subprocess.run(["python", "run_symbol.py", str(RAG_K), str(TEMP), "--n_samples", str(N_SAMPLES)], check=True)
            
    print_results()