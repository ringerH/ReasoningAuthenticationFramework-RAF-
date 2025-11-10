# src/config.py

import os

# --- Project Paths ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BENCHMARK_DIR = os.path.join(PROJECT_ROOT, "data", "test_sets")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "data", "results")

# --- Evaluation Params ---
TOLERANCE = 0.01
SLEEP_TIME = 2

# --- (Optional but Recommended) ---
# You can also move hardcoded params from other files here:
# From problem_generator.py
OPERAND_MIN = 1
OPERAND_MAX = 10

# From test_builder.py
MIN_DEPTH = 0
# (MAX_DEPTH and PROBLEMS_PER_DEPTH are now args, so no longer needed here)