# runner.py
# controlled experimenting
import os, json, glob
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import run_cot
import run_standard
import run_symbol
import run_errfix

def print_results():
    output_dir = run_cot.output_dir
    print("\n" + "="*60)
    print(f"{'PIPELINE':<12} {'ID':<6} {'TRUTH':<10} {'PRED':<10} {'CORRECT'}")
    print("="*60)
    totals = {}
    for pattern, label in [("*_cot.jsonl", "COT"), ("*_standard.jsonl", "STANDARD"),
                            ("*_symbol.jsonl", "LTRAG")]:
        files = glob.glob(os.path.join(output_dir, pattern))
        if not files:
            continue
        correct = total = 0
        for line in open(sorted(files)[-1]):
            d = json.loads(line)
            c = d.get("same", False)
            correct += c
            total += 1
            print(f"{label:<12} {d['id']:<6} {d['label']:<10} {d.get('label-AI','?'):<10} {'y' if c else 'n'}")
        totals[label] = (correct, total)
    print("="*60)
    for name, (c, t) in totals.items():
        print(f"{name:<12} {c}/{t} ({c/t:.1%})")
    print("="*60 + "\n")

# Config
N_SAMPLES = 5
NUM_PROCESSES = 4

RUN_COT = True
RUN_STANDARD = True 
RUN_LTRAG = True 

# run processes

if __name__ == "__main__":
    if RUN_COT:
        run_cot.run_parallel(num_lines=N_SAMPLES, num_processes=NUM_PROCESSES)

    if RUN_STANDARD:
        run_standard.run_parallel(num_lines=N_SAMPLES, num_processes=NUM_PROCESSES)

    if RUN_LTRAG:
        run_symbol.run_parallel(num_lines=N_SAMPLES, num_processes=NUM_PROCESSES)
        run_errfix.run_parallel(num_lines=N_SAMPLES, num_processes=NUM_PROCESSES)

    print_results()

