import json
import os
import sys
import time
import glob # Make sure glob is imported
from datetime import datetime
from typing import List, Dict, Any, Optional

# --- Path Fix ---
# Add the project's root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
# --- End Path Fix ---

# --- Corrected Logger Imports ---
from src.monitoring.logger import setup_logger, get_logger # Import setup and get functions
# --- End Corrected Imports ---

from src.monitoring.tracker import ResultTracker
from src.evaluation.huggingface_client import query_model
from src.evaluation.response_parser import parse_response

# --- Configuration ---
BENCHMARK_DIR = "data/test_sets" # Directory containing benchmark files
RESULTS_DIR = "data/results"
TOLERANCE = 0.01
SLEEP_TIME = 2

# --- Helper attribute to store loaded benchmark filename ---
# Define it here so it's accessible within the scope


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
        logger.error("Please run 'python -m src.generation.test_builder' first.") # Updated instruction
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

def run_evaluation(
    benchmark: List[Dict[str, Any]], tracker: ResultTracker
) -> List[Dict[str, Any]]:
    """
    Steps 2 & 3 (part 1): Run evaluation loop.
    Iterates all problems, calls the API, parses the response,
    and logs the result.
    """
    logger = get_logger() # Get logger instance
    logger.info(f"--- [Step 2 & 3: Run Evaluation] ---")
    results = []

    for i, problem in enumerate(benchmark):
        # Basic check for expected keys
        if not all(k in problem for k in ['level', 'problem', 'answer']):
            logger.warning(f"Skipping invalid problem entry at index {i}: Missing required keys. Data: {problem}")
            continue

        level = problem['level']
        problem_str = problem['problem']
        ground_truth = problem['answer']

        # Ensure ground_truth is a number
        if not isinstance(ground_truth, (int, float)):
             logger.warning(f"Skipping problem {i+1} due to non-numeric ground truth: {ground_truth}")
             continue


        logger.info(f"Running problem {i+1}/{len(benchmark)} (Level {level})...")

        # --- Set defaults for logging ---
        model_answer = None
        is_correct = False
        raw_text_response = "N/A" # Default if API fails or format error

        # --- Step 2a: Call API ---
        prompt = f"What is {problem_str}?"
        response_json = query_model(prompt)

        if response_json is None:
            logger.warning("  - API call failed.")
        else:
            try:
                # --- Step 2b: Parse Response ---
                raw_text_response = response_json['choices'][0]['message']['content']
                model_answer = parse_response(raw_text_response)

                if model_answer is None:
                    logger.warning(f"  - Parser failed to find a number in response: '{raw_text_response[:100]}...'")
                else:
                    # --- Step 3: Check Accuracy (for this one problem) ---
                    # Ensure model_answer is also float for comparison
                    if isinstance(model_answer, (int, float)):
                        is_correct = abs(float(model_answer) - float(ground_truth)) < TOLERANCE
                        logger.info(f"  - Truth: {ground_truth}, Model: {model_answer}, Correct: {is_correct}")
                    else:
                        logger.warning(f"  - Parser returned non-numeric value: {model_answer}. Marking incorrect.")
                        is_correct = False


            except (KeyError, IndexError, TypeError) as e:
                logger.warning(f"  - API response format error: {e}. Full response: {response_json}")
                raw_text_response = f"Format Error: {e}" # Log format error reason

        # --- Log result to tracker file immediately ---
        try:
            tracker.log_result(
                level=level,
                problem=problem_str,
                ground_truth=float(ground_truth), # Ensure float
                model_answer=float(model_answer) if model_answer is not None else None, # Ensure float or None
                is_correct=is_correct
                # Optionally add raw_text_response here if needed in results file
                # raw_response=raw_text_response
            )
        except Exception as track_e:
             logger.error(f"Failed to log result for problem {i+1} to tracker: {track_e}", exc_info=True)


        # --- Rate limiting ---
        logger.debug(f"Sleeping for {SLEEP_TIME} seconds...")
        time.sleep(SLEEP_TIME)

        # Append to in-memory list for immediate calculation
        results.append({'level': level, 'is_correct': is_correct})

    logger.info("--- [Evaluation Complete] ---")
    return results


def calculate_accuracies(results: List[Dict[str, Any]]) -> Dict[int, float]:
    """
    Step 3 (part 2): Calculate the final accuracy for each level.
    """
    logger = get_logger() # Get logger instance
    logger.info(f"--- [Step 3: Calculate Per-Level Accuracy] ---")
    level_counts = {}
    level_correct = {}

    if not results:
         logger.warning("No results to calculate accuracy from.")
         return {}

    for res in results:
         # Add check for expected keys in results list
         if 'level' not in res or 'is_correct' not in res:
              logger.warning(f"Skipping invalid result entry: {res}")
              continue

         level = res['level']
         is_correct = res['is_correct']

         level_counts.setdefault(level, 0)
         level_correct.setdefault(level, 0)

         level_counts[level] += 1
         if is_correct:
             level_correct[level] += 1

    accuracies = {}
    if not level_counts:
        logger.warning("No valid levels found in results.")
        return {}

    # Ensure all levels from min to max are represented, even if 0%
    min_level = min(level_counts.keys())
    max_level = max(level_counts.keys())

    for level in range(min_level, max_level + 1):
        count = level_counts.get(level, 0)
        correct = level_correct.get(level, 0)

        if count == 0:
            acc = 0.0
            # logger.info(f"  Level {level}: 0.00%  (0 / 0)") # Optionally log zero counts
        else:
            acc = (correct / count)
            logger.info(f"  Level {level}: {acc*100:.2f}%  ({correct} / {count})")

        accuracies[level] = acc

    return accuracies


def calculate_cds(accuracies: Dict[int, float]) -> float:
    """
    Steps 4 & 5: Calculate Accuracy Differences and final CDS.
    """
    logger = get_logger() # Get logger instance
    logger.info(f"--- [Step 4 & 5: Calculate CDS] ---")

    if not accuracies:
        logger.error("Accuracy data is empty. Cannot calculate CDS.")
        return 0.0

    sorted_levels = sorted(accuracies.keys())
    # Ensure levels start from at least 0 or 1 for meaningful CDS
    if not sorted_levels or sorted_levels[0] > 1:
        logger.warning(f"Accuracy data does not start near level 0 or 1 ({sorted_levels}). CDS might be less meaningful.")
        # Decide how to handle this - perhaps return 0.0 or calculate based on available levels?
        # For now, proceed but log warning.


    min_level_in_data = min(sorted_levels)
    max_level_in_data = max(sorted_levels)

    # D in the formula should arguably be the intended max depth, not max depth in data
    # Let's assume intended max depth is 10 for consistency, or use max_level_in_data if preferred
    intended_max_D = 10 # Or MAX_DEPTH from config if imported
    D_to_use = max(intended_max_D, max_level_in_data) # Use the larger of intended or actual max level found


    if D_to_use < 1 : # Need at least level 1 to calculate drop from level 2
         logger.warning("Need levels up to at least 1 to calculate CDS.")
         return 0.0 # Or maybe 1.0 if no decay is possible? Returning 0.0 as per previous logic.

    total_drop = 0
    # Sum drops from level 1 up to D_to_use
    # Original formula sums from d=2 to D. Let's stick to that.
    # We need accuracy for d-1, so need data for level 1 if summing from d=2.
    if 1 not in accuracies and 0 not in accuracies and D_to_use >=2 :
         logger.warning("Missing accuracy for level 1 (and 0), cannot calculate drop from L2 vs L1.")
         # Decide if CDS is still valid - perhaps start sum from d=3? For now, continue but log.

    start_calc_level = 2 # As per formula
    valid_drops_calculated = 0

    for d in range(start_calc_level, D_to_use + 1):
        # We need accuracy for level d-1 to calculate the drop
        if (d-1) not in accuracies:
            logger.warning(f"Missing accuracy for level {d-1}, cannot calculate drop for level {d}. Skipping.")
            continue # Skip this drop calculation

        acc_d = accuracies.get(d, 0.0) # Assume 0% if level d is missing (post-failure)
        acc_d_minus_1 = accuracies.get(d-1, 0.0) # We know d-1 exists from check above

        drop = abs(acc_d - acc_d_minus_1)
        logger.info(f"    - Drop (L{d} vs L{d-1}): |{acc_d*100:.2f}% - {acc_d_minus_1*100:.2f}%| = {drop*100:.2f}%")
        total_drop += drop
        valid_drops_calculated += 1


    # If no valid drops could be calculated (e.g., only had level 0 data)
    if D_to_use == 0 or valid_drops_calculated == 0:
        logger.warning("Could not calculate any valid drops. Returning default CDS.")
        # What should default be? 1.0 (no decay observed) or 0.0? Let's assume 1.0 (perfect stability).
        return 1.0

    # Original formula divides by D (max depth).
    avg_drop = total_drop / D_to_use

    # Final CDS = 1 - Avg_Drop
    cds_score = 1.0 - avg_drop

    logger.info(f"\n  Total Drop Sum: {total_drop*100:.2f}% (based on {valid_drops_calculated} differences)")
    logger.info(f"  Max Depth (D) used for avg: {D_to_use}")
    logger.info(f"  Average Drop (Total Drop / D): {avg_drop*100:.4f}%")

    # Ensure CDS is within [0, 1] range
    cds_score = max(0.0, min(1.0, cds_score))

    return cds_score


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
    benchmark = load_benchmark(BENCHMARK_DIR) # Pass the directory to search
    if not benchmark:
        logger.error("Benchmark loading failed. Exiting.")
        return

    # Step 2 & 3 (part 1): Run evaluation
    results = run_evaluation(benchmark, tracker)

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