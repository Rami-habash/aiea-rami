"""Load JSONL results and calculate evaluation metrics."""
import json
from pathlib import Path


def load_and_calculate_results(outputs, model, price_table):
    """Load each file once, then calculate results for each method."""
    paths = {Path(path).resolve() for output in outputs.values()
             for path in [output["predictions_file"], *output["usage_files"]]}
    loaded_rows = {path: read_jsonl(path) for path in paths}
    prices = price_table[model]
    results = {}
    for method, output in outputs.items():
        rows = loaded_rows[Path(output["predictions_file"]).resolve()]
        usage_paths = dict.fromkeys(Path(path).resolve() for path in output["usage_files"])
        usage_rows = [row for path in usage_paths for row in loaded_rows[path]]

        result = classification_metrics(rows)
        result.update(answer_metrics(rows))
        tokens = compute_tokens(usage_rows)
        result.update({
            "predictions_file": output["predictions_file"],
            "sample_ids": [row.get("id") for row in rows],
            "rows": rows,
            "tokens": tokens,
            "estimated_cost_usd": compute_price(tokens, prices),
            "usage_complete": all(bool(row.get("usage")) for row in usage_rows),
        })
        results[method] = result
    return results


def read_jsonl(path):
    """Read a JSONL file into rows."""
    with open(path, encoding="utf-8") as infile:
        return [json.loads(line) for line in infile if line.strip()]


# Sandard classification metrics
def classification_metrics(rows):
    labels = ["True", "False", "Unknown"]
    matrix = {actual: {pred: 0 for pred in labels + ["Error"]} for actual in labels}
    invalid_labels = 0
    for row in rows:
        actual, predicted = row.get("label"), row.get("label-AI")
        if actual not in labels:
            invalid_labels += 1
            continue
        matrix[actual][predicted if predicted in labels else "Error"] += 1
    per_label = {}
    for label in labels:
        # Measurements
        true_positives = matrix[label][label]
        support = sum(matrix[label].values())
        predicted_count = sum(matrix[actual][label] for actual in labels)
        precision = true_positives / predicted_count if predicted_count else 0.0
        recall = true_positives / support if support else 0.0
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
            "support": support,
        }

    correct = sum(matrix[label][label] for label in labels)

    # All reported metrics:
    return {
        "total": len(rows),
        "correct": correct,
        "accuracy": correct / len(rows) if rows else None,
        "errors": sum(row.get("label-AI") not in labels for row in rows),
        "invalid_ground_truth": invalid_labels,
        "confusion_matrix": matrix,
        "confusion_matrix_axes": {"rows": "actual", "columns": "predicted"},
        "per_label": per_label,
        "macro_average": {
            metric: sum(per_label[label][metric] for label in labels) / len(labels)
            for metric in ("precision", "recall", "f1")
        },
    }

# Metrics relate to the answer and unknown rates
def answer_metrics(rows):
    """Calculate Unknown and True/False prediction rates from rows."""
    valid_rows = [row for row in rows if row.get("label") in ("True", "False", "Unknown")]
    definite = sum(row.get("label-AI") in ("True", "False") for row in valid_rows)
    definite_correct = sum(row.get("label-AI") in ("True", "False")
                           and row["label-AI"] == row["label"] for row in valid_rows)
    unknown = sum(row.get("label-AI") == "Unknown" for row in valid_rows)
    unknown_correct = sum(row["label"] == "Unknown" and row.get("label-AI") == "Unknown"
                          for row in valid_rows)
    actual_unknown = sum(row["label"] == "Unknown" for row in valid_rows)
    total = len(rows)

    # calculate and return metrics
    return {
        "definite_answer_accuracy": definite_correct / definite if definite else None,
        "definite_answer_rate": definite / total if total else None,
        "unknown_precision": unknown_correct / unknown if unknown else None,
        "unknown_recall": unknown_correct / actual_unknown if actual_unknown else None,
    }


# computes total tokens used in the supplied rows
def compute_tokens(rows):
    """Sum saved token usage."""
    totals = {"input": 0, "cached_input": 0, "output": 0, "reasoning": 0}
    for row in rows:
        usage = row.get("usage") or {}
        totals["input"] += usage.get("in", 0)
        totals["cached_input"] += usage.get("cached", 0)
        totals["output"] += usage.get("out", 0)
        totals["reasoning"] += usage.get("reasoning", 0)
    return totals


def compute_price(tokens, prices):
    """Compute cost using rates per million tokens."""
    input_rate, cached_input_rate, output_rate = prices
    uncached_input = tokens["input"] - tokens["cached_input"]
    input_cost = uncached_input * input_rate
    cached_input_cost = tokens["cached_input"] * cached_input_rate
    output_cost = tokens["output"] * output_rate
    total_cost_usd = (input_cost + cached_input_cost + output_cost) / 1e6
    return total_cost_usd
