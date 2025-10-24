import json
import os
import sys

# --- Path Fix ---
# Add the project's root directory to the Python path
# This is needed to find 'src' when running this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# --- End Path Fix ---

# --- Corrected Imports ---
# Import the function to get the logger and timestamp
from src.monitoring.logger import get_logger, get_run_timestamp
from src.generation.problem_generator import generate_problem
# --- End Corrected Imports ---

# --- Get the logger instance ---
logger = get_logger()
# --- End Get logger ---

from datetime import datetime

# --- Configuration ---
MIN_DEPTH = 0
MAX_DEPTH = 10
PROBLEMS_PER_DEPTH = 3
OUTPUT_DIR = "data/test_sets"

# --- Get timestamp FROM logger and define OUTPUT_FILE ---
# Get the timestamp that the logger was initialized with (or generated)
run_timestamp = get_run_timestamp()
if run_timestamp is None:
    # Fallback just in case, though get_logger() should ensure it's set
    logger.warning("Could not get timestamp from logger, generating a fallback.")
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"stratified_benchmark_{run_timestamp}.jsonl")
# --- End Timestamp Handling ---

def build_test_set():
    """
    Generates the complete test set and saves it to a .jsonl file.
    """
    logger.info("--- [Test Set Builder Started] ---")

    # Ensure the output directory exists
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    except OSError as e:
        logger.error(f"Could not create directory {OUTPUT_DIR}. {e}", exc_info=True) # Added exc_info
        return

    logger.info(f"Generating test set at: {OUTPUT_FILE}")
    logger.info(f"Params: Levels {MIN_DEPTH}-{MAX_DEPTH}, {PROBLEMS_PER_DEPTH} problems per level.")

    total_problems = 0
    try:
        # Open the file in 'write' mode ('w') to create a new test set
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:

            for depth in range(MIN_DEPTH, MAX_DEPTH + 1):
                # Log progress less verbosely, maybe use debug level
                logger.debug(f"Generating problems for level {depth}...")

                generated_count = 0
                while generated_count < PROBLEMS_PER_DEPTH:
                    try:
                        # 1. Generate a single problem
                        problem_str, correct_answer = generate_problem(depth)

                        # 2. Create the JSON data entry
                        data_entry = {
                            "level": depth,
                            "problem": problem_str,
                            "answer": correct_answer
                        }

                        # 3. Write it as a new line in the .jsonl file
                        f.write(json.dumps(data_entry) + "\n")
                        total_problems += 1
                        generated_count += 1
                    # Catch potential errors during problem generation itself
                    except ValueError as ve:
                        logger.warning(f"Problem generation failed for depth {depth}: {ve}. Retrying...")
                        continue # Try generating another problem for this depth
                    except Exception as gen_e:
                         logger.error(f"Unexpected error during generation for depth {depth}: {gen_e}", exc_info=True)
                         # Decide whether to continue or stop
                         continue


    except IOError as e:
        logger.error(f"Could not write to file {OUTPUT_FILE}. {e}", exc_info=True)
        return
    except Exception as e:
        logger.error(f"An unexpected error occurred during build_test_set: {e}", exc_info=True)
        return

    logger.info(f"Successfully generated {total_problems} problems.")
    logger.info(f"Test set saved to {OUTPUT_FILE}")
    logger.info("--- [Build Complete] ---")


if __name__ == "__main__":
    build_test_set()