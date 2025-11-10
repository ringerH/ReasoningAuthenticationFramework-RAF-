# src/utils.py

import json
import os
import glob
from typing import List, Dict, Any, Optional
from src.monitoring.logger import get_logger
from src.config import BENCHMARK_DIR # <-- Import from your new config

# --- Move the entire function from main.py here ---

def load_benchmark() -> Optional[List[Dict[str, Any]]]:
    """
    Step 1: Loads the LATEST benchmark problem file from the directory.
    """
    logger = get_logger()
    logger.info("--- [Step 1: Load Benchmark] ---")

    # Use the imported config path
    list_of_files = glob.glob(os.path.join(BENCHMARK_DIR, 'stratified_benchmark_*.jsonl'))
    if not list_of_files:
        logger.error(f"No benchmark files found in {BENCHMARK_DIR}")
        logger.error("Please run 'python -m src.generation.test_builder' first.")
        return None

    try:
        latest_file = max(list_of_files, key=os.path.getctime)
    except ValueError:
        logger.error(f"Error finding latest file in {BENCHMARK_DIR}")
        return None

    filepath = latest_file
    logger.info(f"Loading latest benchmark file: {os.path.basename(filepath)}")

    # Store the loaded file path
    load_benchmark.last_loaded_file = filepath

    benchmark = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    stripped_line = line.strip()
                    if stripped_line:
                        benchmark.append(json.loads(stripped_line))
                except json.JSONDecodeError as e:
                     logger.warning(f"Skipping invalid JSON line {line_num}: '{line.strip()}'. {e}")
                     continue
    except IOError as e:
        logger.error(f"Error reading file {filepath}: {e}", exc_info=True)
        return None
    
    if not benchmark:
        logger.warning(f"Benchmark file {os.path.basename(filepath)} loaded but was empty.")
        return None

    logger.info(f"Loaded {len(benchmark)} problems from {os.path.basename(filepath)}.")
    return benchmark

load_benchmark.last_loaded_file = "Unknown"