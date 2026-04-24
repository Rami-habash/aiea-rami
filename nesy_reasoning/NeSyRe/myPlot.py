# myPlot.py
# Bar graph comparing baseline vs neurosymbolic RAG (LINC+) accuracy across LLMs

import matplotlib.pyplot as plt
import numpy as np


def plot_results(results: dict):
    """
    result json file like:
    {
        "proofwriter": {"gpt-3.5-turbo": {"baseline": 0.62, "neurosymbolic": 0.78}, ...},
        "folio":       {"gpt-3.5-turbo": {"baseline": 0.55, "neurosymbolic": 0.70}, ...}
    }
    """
    tasks = list(results.keys())
    fig, axes = plt.subplots(1, len(tasks), figsize=(8 * len(tasks), 5))

    # if only pw or only fol
    if len(tasks) == 1:
        axes = [axes]

    # find and graph values for each task
    for ax, task in zip(axes, tasks):
        models = list(results[task].keys()) 
        baseline_scores = [results[task][m]["baseline"] * 100 for m in models]
        linc_scores = [results[task][m]["neurosymbolic"] * 100 for m in models]

        x = np.arange(len(models))
        width = 0.35

        bars_baseline = ax.bar(x - width / 2, baseline_scores, width, label="Baseline (zero-shot)", color="#D44131")
        bars_linc = ax.bar(x + width / 2, linc_scores, width, label="myLINC (Agentic RAG Relevance)", color="#A12CBE")

        ax.set_xlabel("Model")
        ax.set_ylabel("Accuracy (%)")
        ax.set_title(f"{task.capitalize()}: Baseline vs myLINC\n")
        ax.set_xticks(x)
        ax.set_xticklabels(models)
        ax.set_ylim(0, 100)
        ax.legend()

        for bar in bars_baseline:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{bar.get_height():.0f}%", ha="center", va="bottom", fontsize=9)
        for bar in bars_linc:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{bar.get_height():.0f}%", ha="center", va="bottom", fontsize=9)

    # fit and save
    plt.tight_layout()
    plt.savefig("results.png", dpi=150)
    plt.show()
    print("Saved to results.png")


if __name__ == "__main__":
    import json, os
    # load json
    results_path = os.path.join(os.path.dirname(__file__), "performance.json")
    with open(results_path) as f:
        results = json.load(f)
    plot_results(results) 
