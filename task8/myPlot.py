# myPlot.py
# Bar graph comparing baseline vs neurosymbolic RAG (LINC+) accuracy across LLMs

import matplotlib.pyplot as plt
import numpy as np


def plot_results(results: dict):
    """
    result json file like: 
    {
        "gpt-3.5-turbo": {"baseline": 0.62, "neurosymbolic": 0.78},
        "gpt-4o-mini": {"baseline": 0.50, "neurosymbolic": 0.64},
    }
    """

    models = list(results.keys())
    baseline_scores = [results[m]["baseline"] * 100 for m in models]
    linc_scores = [results[m]["neurosymbolic"] * 100 for m in models]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))

    bars_baseline = ax.bar(x - width / 2, baseline_scores, width, label="Baseline (zero-shot)", color="#D44131")
    bars_linc = ax.bar(x + width / 2, linc_scores, width, label="LINC+ (neurosymbolic + RAG)", color="#A12CBE")

    ax.set_xlabel("Model")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Baseline vs LINC+ Accuracy by LLM")
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 100)
    ax.legend()

    # label each bar with its value
    for bar in bars_baseline:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{bar.get_height():.0f}%", ha="center", va="bottom", fontsize=9)
    for bar in bars_linc:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{bar.get_height():.0f}%", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plt.savefig("results.png", dpi=150)
    plt.show()
    print("Saved to results.png")


if __name__ == "__main__":
    import json, os
    results_path = os.path.join(os.path.dirname(__file__), "performance.json")
    with open(results_path) as f:
        results = json.load(f)
    plot_results(results) 
