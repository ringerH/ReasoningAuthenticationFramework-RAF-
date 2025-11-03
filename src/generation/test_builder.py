import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.monitoring.logger import get_logger, get_run_timestamp
from src.generation.problem_generator import generate_problem

logger = get_logger()

MIN_DEPTH = 0
MAX_DEPTH = 5
PROBLEMS_PER_DEPTH =20

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "test_sets")

run_timestamp = get_run_timestamp()
if run_timestamp is None:
    logger.warning("Could not get timestamp from logger, generating a fallback.")
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"stratified_benchmark_{run_timestamp}.jsonl")


def build_test_set():
    logger.info("--- [Test Set Builder Started] ---")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Output directory: {OUTPUT_DIR}")

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logger.info(f"Ensured output directory exists: {OUTPUT_DIR}")
    except OSError as e:
        logger.error(f"Could not create directory {OUTPUT_DIR}. {e}", exc_info=True)
        return

    logger.info(f"Generating test set at: {OUTPUT_FILE}")
    logger.info(f"Params: Levels {MIN_DEPTH}-{MAX_DEPTH}, {PROBLEMS_PER_DEPTH} problems per level.")

    total_problems = 0
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for depth in range(MIN_DEPTH, MAX_DEPTH + 1):
                logger.info(f"Generating problems for level {depth}...")

                generated_count = 0
                while generated_count < PROBLEMS_PER_DEPTH:
                    try:
                        # Generate a single problem
                        problem_str, correct_answer = generate_problem(depth)

                        # Create the JSON data entry
                        data_entry = {
                            "level": depth,
                            "problem": problem_str,
                            "answer": correct_answer
                        }

                        # Write it as a new line in the .jsonl file
                        f.write(json.dumps(data_entry) + "\n")
                        total_problems += 1
                        generated_count += 1
                        
                    except ValueError as ve:
                        logger.warning(f"Problem generation failed for depth {depth}: {ve}. Retrying...")
                        continue
                    except Exception as gen_e:
                        logger.error(f"Unexpected error during generation for depth {depth}: {gen_e}", exc_info=True)
                        continue

                logger.info(f" Generated {generated_count} problems for level {depth}")

    except IOError as e:
        logger.error(f"Could not write to file {OUTPUT_FILE}. {e}", exc_info=True)
        return
    except Exception as e:
        logger.error(f"An unexpected error occurred during build_test_set: {e}", exc_info=True)
        return

    logger.info(f"\nSuccessfully generated {total_problems} problems.")
    logger.info(f"Test set saved to: {OUTPUT_FILE}")
    
    # Verify the file was created
    if os.path.exists(OUTPUT_FILE):
        file_size = os.path.getsize(OUTPUT_FILE)
        logger.info(f"File verified: {file_size} bytes")
    else:
        logger.error(f"File was not created at expected location: {OUTPUT_FILE}")
    
    logger.info("--- [Build Complete] ---")


if __name__ == "__main__":
    build_test_set()