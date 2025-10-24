import json
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


try:
    from src.monitoring.logger import logger
except ImportError:
   
    import logging
    logger = logging.getLogger(__name__)


class ResultTracker:
  
    
    def __init__(self, filepath: str):
       
        self.filepath = filepath
        self._prepare_directory()

    def _prepare_directory(self):
       
        directory = os.path.dirname(self.filepath)
        try:
            os.makedirs(directory, exist_ok=True)
            # Test write access by opening the file in append mode
            with open(self.filepath, 'a', encoding='utf-8') as f:
                pass
            logger.info(f"ResultTracker initialized. Logging results to {self.filepath}")
        except (OSError, IOError) as e:
            logger.error(f"Failed to create/access tracker file at {self.filepath}. {e}")
            raise  # Stop the program if we can't write results

    def log_result(
        self, 
        level: int, 
        problem: str, 
        ground_truth: float, 
        model_answer: Optional[float], 
        is_correct: bool
    ):
        
        result_entry = {
            "level": level,
            "problem": problem,
            "ground_truth": ground_truth,
            "model_answer": model_answer,
            "is_correct": is_correct
        }
        
        try:
           
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result_entry) + "\n")
        except IOError as e:
            logger.error(f"Failed to write result to {self.filepath}. Data: {result_entry}. {e}")


# --- Self-Test Block ---
if __name__ == "__main__":
   
    logger.info("--- [ResultTracker Self-Test] ---")
    
    TEST_FILE = "data/results/tracker_selftest.jsonl"
    
    
    if os.path.exists(TEST_FILE):
        try:
            os.remove(TEST_FILE)
            logger.info(f"Removed old test file: {TEST_FILE}")
        except OSError as e:
            logger.warning(f"Could not remove old test file: {e}")
            
    try:
        # 1. Initialize tracker
        tracker = ResultTracker(TEST_FILE)
        
        # 2. Log 3 test results
        logger.info("Logging 3 test results...")
        tracker.log_result(level=0, problem="1 + 1", ground_truth=2.0, model_answer=2.0, is_correct=True)
        tracker.log_result(level=1, problem="(2 * 3)", ground_truth=6.0, model_answer=5.0, is_correct=False)
        tracker.log_result(level=1, problem="(5 - 1)", ground_truth=4.0, model_answer=None, is_correct=False)
        
        logger.info(f"Self-test complete. Please check the file: {TEST_FILE}")
        
        # 3. Read back the file to verify
        with open(TEST_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        if len(lines) == 3:
            logger.info(f"Verified {len(lines)} lines written to file. PASS.")
        else:
            logger.error(f"Verification failed! Expected 3 lines, found {len(lines)}. FAIL.")

    except Exception as e:
        logger.error(f"Self-test failed with an exception: {e}", exc_info=True)