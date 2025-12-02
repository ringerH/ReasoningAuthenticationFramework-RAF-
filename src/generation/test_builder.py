import json
import os
import sys
import argparse
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.monitoring.logger import get_logger, get_run_timestamp
# Import the new linear generator function
from src.generation.problem_generator import generate_problem_by_ops

logger = get_logger()

# Define Project Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "test_sets")

def build_test_set(max_ops: int, problems_per_level: int, step_size: int = 2):
    """
    Generates a stratified benchmark test set based on Operation Count (Linear Scaling).
    
    Args:
        max_ops (int): The maximum number of operations to test (e.g., 30).
        problems_per_level (int): Number of problems to generate for each complexity step.
        step_size (int): The interval between complexity steps (e.g., 2 -> 1 op, 3 ops, 5 ops...).
    """
    
    # 1. Setup Timestamp & Filename
    run_timestamp = get_run_timestamp()
    if run_timestamp is None:
        logger.warning("Could not get timestamp from logger, generating a fallback.")
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"stratified_benchmark_{run_timestamp}.jsonl")

    # 2. Setup Logging & Directory
    logger.info("--- [Test Set Builder Started] ---")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Output directory: {OUTPUT_DIR}")

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    except OSError as e:
        logger.error(f"Could not create directory {OUTPUT_DIR}. {e}", exc_info=True)
        return

    # 3. Log Parameters
    logger.info(f"Generating test set at: {OUTPUT_FILE}")
    logger.info(f"Params: Linear scaling 1 to {max_ops} ops, Step={step_size}, N={problems_per_level}")

    total_problems = 0
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            
            # --- LOOP: Iterate by Operation Count (Linear) ---
            # Start at 1 op, go up to max_ops, jumping by step_size
            for current_ops in range(1, max_ops + 1, step_size):
                logger.info(f"Generating problems for Complexity: {current_ops} operations...")

                generated_count = 0
                
                while generated_count < problems_per_level:
                    try:
                        # Call the NEW linear generator
                        problem_str, correct_answer = generate_problem_by_ops(current_ops)

                        # Create the JSON data entry
                        # We use 'level' to store the Op Count so downstream tools (evaluator)
                        # don't need to change their variable names yet.
                        data_entry = {
                            "level": current_ops,  # Represents Complexity (Num Ops)
                            "problem": problem_str,
                            "answer": correct_answer
                        }

                        # Write to file
                        f.write(json.dumps(data_entry) + "\n")
                        total_problems += 1
                        generated_count += 1
                        
                    except ValueError as ve:
                        logger.warning(f"Generation failed for ops={current_ops}: {ve}. Retrying...")
                        continue
                    except Exception as gen_e:
                        logger.error(f"Unexpected error at ops={current_ops}: {gen_e}", exc_info=True)
                        continue

                logger.info(f" -> Generated {generated_count} problems for {current_ops} ops.")

    except IOError as e:
        logger.error(f"Could not write to file {OUTPUT_FILE}. {e}", exc_info=True)
        return
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return

    # 4. Final Verification
    logger.info(f"\nSuccessfully generated {total_problems} problems.")
    logger.info(f"Test set saved to: {OUTPUT_FILE}")
    
    if os.path.exists(OUTPUT_FILE):
        file_size = os.path.getsize(OUTPUT_FILE)
        logger.info(f"File verified: {file_size} bytes")
    else:
        logger.error(f"File was not created at expected location: {OUTPUT_FILE}")
    
    logger.info("--- [Build Complete] ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a linear complexity benchmark test set.")
    
    parser.add_argument(
        '-m', '--max-ops',
        type=int,
        default=30,
        help='Maximum number of operations (complexity limit). Default: 30'
    )
    
    parser.add_argument(
        '-n', '--num-problems',
        type=int,
        default=10,
        help='Number of problems to generate per complexity step. Default: 10'
    )
    
    parser.add_argument(
        '-s', '--step',
        type=int,
        default=2,
        help='Step size for complexity (e.g., 2 means 1, 3, 5, 7 ops). Default: 2'
    )
    
    args = parser.parse_args()

    # Call the builder function with the parsed arguments
    build_test_set(
        max_ops=args.max_ops, 
        problems_per_level=args.num_problems, 
        step_size=args.step
    )