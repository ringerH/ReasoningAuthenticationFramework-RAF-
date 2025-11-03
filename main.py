import json
import os
import sys
import glob 
from datetime import datetime
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


from src.monitoring.logger import setup_logger, get_logger
from src.monitoring.tracker import ResultTracker

from src.analysis.evaluator import run_evaluation
from src.analysis.calculator import calculate_accuracies, calculate_cds

BENCHMARK_DIR = "data/test_sets" 
RESULTS_DIR = "data/results"
TOLERANCE = 0.01
SLEEP_TIME = 2




def load_benchmark(benchmark_dir: str) -> Optional[List[Dict[str, Any]]]:
    """
    Step 1: Loads the LATEST benchmark problem file from the directory.
    """
    # Get logger instance within the function
    logger = get_logger()
    logger.info("--- [Step 1: Load Benchmark] ---")

    # Find the most recent benchmark file
    list_of_files = glob.glob(os.path.join(benchmark_dir, 'stratified_benchmark_*.jsonl'))
    if not list_of_files:
        logger.error(f"No benchmark files found in {benchmark_dir}")
        logger.error("Please run 'python -m src.generation.test_builder' first.")
        return None

    try:
        latest_file = max(list_of_files, key=os.path.getctime)
    except ValueError:
        logger.error(f"Error finding latest file in {benchmark_dir} (maybe empty or contains invalid files)")
        return None

    filepath = latest_file
    logger.info(f"Loading latest benchmark file: {os.path.basename(filepath)}")

    # Store the loaded file path for reporting using the function attribute
    load_benchmark.last_loaded_file = filepath

    benchmark = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    # Strip whitespace which might cause issues
                    stripped_line = line.strip()
                    if stripped_line: # Avoid processing empty lines
                        benchmark.append(json.loads(stripped_line))
                except json.JSONDecodeError as e:
                     logger.warning(f"Skipping invalid JSON line {line_num} in {os.path.basename(filepath)}: '{line.strip()}'. Error: {e}")
                     continue # Skip bad lines
    except IOError as e:
        logger.error(f"Error reading file {filepath}: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading benchmark file {filepath}: {e}", exc_info=True)
        return None


    if not benchmark:
        logger.warning(f"Benchmark file {os.path.basename(filepath)} loaded but contained no valid problems.")
        return None

    logger.info(f"Loaded {len(benchmark)} problems from {os.path.basename(filepath)}.")
    return benchmark

load_benchmark.last_loaded_file = "Unknown"

def main():
    """
    Main orchestration function.
    """
    # --- Generate timestamp and setup logger FIRST ---
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Setup logger with timestamp - critical to do this first
    logger = setup_logger(run_timestamp)

    logger.info(f"====== [New Benchmark Run Started: {run_timestamp}] ======")

    # --- Setup Tracker with the SAME timestamp ---
    results_filename = os.path.join(RESULTS_DIR, f"run_{run_timestamp}.jsonl")
    try:
        tracker = ResultTracker(results_filename)
    except Exception as e:
        logger.error(f"Failed to initialize ResultTracker at {results_filename}. Exiting.", exc_info=True)
        return # Exit if tracker fails

    # Step 1: Load (pass directory now)
    benchmark = load_benchmark(BENCHMARK_DIR) 
    if not benchmark:
        logger.error("Benchmark loading failed. Exiting.")
        return

    # Step 2 & 3 (part 1): Run evaluation
    results = run_evaluation(benchmark, tracker, TOLERANCE, SLEEP_TIME)

    # Step 3 (part 2): Calculate Accuracies
    accuracies = calculate_accuracies(results)

    # Step 4 & 5: Calculate CDS
    cds_score = calculate_cds(accuracies)

    # --- Final Report ---
    logger.info("\n" + "="*30)
    logger.info("--- [FINAL BENCHMARK REPORT] ---")
    logger.info(f"Results file: {results_filename}")
    # Use the stored attribute to get the loaded benchmark filename
    logger.info(f"Benchmark file used: {os.path.basename(load_benchmark.last_loaded_file)}")
    logger.info("="*30)
    logger.info("\nPer-Level Accuracy:")
    # Check if accuracies dictionary is populated before iterating
    if accuracies:
        # Report for all levels present in the calculation range
        all_levels = sorted(accuracies.keys())
        if all_levels:
            min_l, max_l = min(all_levels), max(all_levels)
            for level in range(min_l, max_l + 1):
                 acc = accuracies.get(level, 0.0) # Get accuracy or default to 0.0 if missing
                 logger.info(f"  Level {level}: {acc*100:.2f}%")
        else:
            logger.warning("Accuracy dictionary was empty.")

    else:
        logger.warning("No accuracy results to report.")

    # Check if cds_score exists and is valid before reporting
    if isinstance(cds_score, float):
         logger.info(f"\nCompositional Decay Score (CDS): {cds_score:.4f}")
    else:
         logger.warning("CDS score could not be calculated or was invalid.")

    logger.info("\n--- [Report Complete] ---")
    logger.info(f"====== [Benchmark Run Finished: {run_timestamp}] ======\n")

if __name__ == "__main__":
    main()