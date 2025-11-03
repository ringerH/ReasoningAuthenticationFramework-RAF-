import json
import os
import sys
import time
from typing import List, Dict, Any, Optional

# --- Path Fix ---
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# --- End Path Fix ---

from src.monitoring.logger import get_logger
from src.monitoring.tracker import ResultTracker
from src.evaluation.huggingface_client import query_model
from src.evaluation.response_parser import parse_response

def run_evaluation(
    benchmark: List[Dict[str, Any]], 
    tracker: ResultTracker,
    tolerance: float,
    sleep_time: float
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
        prompt = problem_str
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
                        is_correct = abs(float(model_answer) - float(ground_truth)) < tolerance
                        logger.info(f"  - Truth: {ground_truth}, Model: {model_answer}, Correct: {is_correct}")
                    else:
                        logger.warning(f"  - Parser returned non-numeric value: {model_answer}. Marking incorrect.")
                        is_correct = False


            except (KeyError, IndexError, TypeError) as e:
                logger.warning(f"  - API response format error: {e}. Full response: {json.dumps(response_json)}")
                raw_text_response = f"Format Error: {e}" 

        try:
            tracker.log_result(
                level=level,
                problem=problem_str,
                ground_truth=float(ground_truth), # Ensure float
                model_answer=float(model_answer) if model_answer is not None else None, # Ensure float or None
                is_correct=is_correct,
                raw_response=raw_text_response 
            )
        except Exception as track_e:
             logger.error(f"Failed to log result for problem {i+1} to tracker: {track_e}", exc_info=True)


        
        logger.debug(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)

    
        results.append({'level': level, 'is_correct': is_correct})

    logger.info("--- [Evaluation Complete] ---")
    return results