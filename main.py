# main.py (New, Thinner Version)

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# --- 1. Import from new modules ---
from src.config import RESULTS_DIR, TOLERANCE, SLEEP_TIME
from src.utils import load_benchmark
from src.analysis.reporting import log_final_report

# --- 2. Standard imports ---
from src.monitoring.logger import setup_logger, get_logger
from src.monitoring.tracker import ResultTracker
from src.analysis.evaluator import run_evaluation
from src.analysis.calculator import calculate_accuracies, calculate_cds

# --- 3. load_benchmark() function is GONE ---

def main():
    """
    Main orchestration function.
    """
    # --- Setup ---
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = setup_logger(run_timestamp)
    logger.info(f"====== [New Benchmark Run Started: {run_timestamp}] ======")

    results_filename = os.path.join(RESULTS_DIR, f"run_{run_timestamp}.jsonl")
    try:
        tracker = ResultTracker(results_filename)
    except Exception as e:
        logger.error(f"Failed to initialize ResultTracker. Exiting.", exc_info=True)
        return

    # --- 4. Pipeline Steps ---
    # Step 1: Load (Now cleaner)
    benchmark = load_benchmark() 
    if not benchmark:
        logger.error("Benchmark loading failed. Exiting.")
        return

    # Step 2 & 3: Run evaluation
    results = run_evaluation(benchmark, tracker, TOLERANCE, SLEEP_TIME)

    # Step 3 (part 2): Calculate Accuracies
    accuracies = calculate_accuracies(results)

    # Step 4 & 5: Calculate CDS
    cds_score = calculate_cds(accuracies)

    # --- 5. Final Report (Now a clean, single function call) ---
    log_final_report(
        accuracies=accuracies,
        cds_score=cds_score,
        results_filename=os.path.basename(results_filename),
        benchmark_filename=os.path.basename(load_benchmark.last_loaded_file)
    )

    logger.info(f"====== [Benchmark Run Finished: {run_timestamp}] ======\n")


if __name__ == "__main__":
    main()