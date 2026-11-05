"""Run from FOLIO_framework with: python -u -m runner.main."""
# controlled experimenting
import os
import shutil
import time
from datetime import datetime, timezone

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from . import settings
from .methods import run_cot, run_standard, run_symbol, run_errfix
from config.Settings import config

def configure_agents(model, effort):
    """Apply the experiment model, reasoning effort, and output directory to all agents."""
    # Agent settings remain in config/config.yaml; experiment overrides come from settings.py.
    for role in ("extra", "symbol", "cot", "standard", "errfix"):
        config["agent"][role]["model"] = model
        if role != "extra":
            config["agent"][role]["reasoning_effort"] = effort
    # Methods initialize paths at import; redirect them to the model chosen for this run.
    model_name = model.split("/")[-1] if "/" in model else model
    output_dir = f"./data.nosync/{config['task']}/{model_name}"
    os.makedirs(output_dir, exist_ok=True)
    for method in (run_cot, run_standard, run_symbol, run_errfix):
        method.output_dir = output_dir
    run_errfix.sym_model_name = model_name


def run_methods(n_samples, num_workers):
    """Run enabled methods and return prediction and billed-usage paths per pipeline."""
    outputs = {}
    if settings.RUN_COT:
        outputs["COT"] = run_cot.run_parallel(num_lines=n_samples, num_processes=num_workers)

    if settings.RUN_STANDARD:
        outputs["STANDARD"] = run_standard.run_parallel(num_lines=n_samples, num_processes=num_workers)

    if settings.RUN_LTRAG:
        config["agent"]["symbol"]["cot"] = settings.LTRAG_COT
        config["agent"]["errfix"]["cot"] = settings.LTRAG_COT
        symbol_output = run_symbol.run_parallel(num_lines=n_samples, num_processes=num_workers)
        repair_output = run_errfix.run_parallel(num_lines=n_samples, num_processes=num_workers)

        outputs["LTRAG"] = {
            "predictions_file": repair_output["predictions_file"],
            "usage_files": symbol_output["usage_files"] + repair_output["usage_files"],
        }
    return outputs


def main():
    """Run configured experiments and preserve their detailed JSONL outputs."""
    # Share one archive timestamp across this invocation’s model and effort combinations.
    run_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S-%fZ")
    for model in settings.MODELS:
        for effort in settings.EFFORTS:
            print(f"\n{'#'*60}\n# mode={model} effort={effort}\n{'#'*60}")
            configure_agents(model, effort)
            start = time.monotonic()
            outputs = run_methods(settings.N_SAMPLES, settings.NUM_WORKERS)
            duration = time.monotonic() - start
            # Archive only the prediction and usage files returned by this experiment.
            archive_files = {path for output in outputs.values()
                            for path in [output["predictions_file"], *output["usage_files"]]}
            archive_dir = os.path.join("runs_archive", model.split("/")[-1], run_stamp)
            os.makedirs(archive_dir, exist_ok=True)
            for path in archive_files:
                shutil.copy2(path, os.path.join(archive_dir, os.path.basename(path)))
            print(f"Finished in {duration:.1f}s. JSONL files archived in {archive_dir}")
            for method, output in outputs.items():
                print(f"{method}: {output['predictions_file']}")



if __name__ == "__main__":
    main()
