# src/config.py

import os

# --- Project Paths ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BENCHMARK_DIR = os.path.join(PROJECT_ROOT, "data", "test_sets")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "data", "results")

# --- Evaluation Params ---
TOLERANCE = 0.01
SLEEP_TIME = 2

OPERAND_MIN = 1
OPERAND_MAX = 10

ICCR_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "iccr_test_sets")

ICCR_CONFIG = {
    "BENCHMARK_SIZE":100,
    # 10 queries is tight but forces efficiency. 
    # Max usage = 10 API calls + 1 Final Answer call.
    "BUDGET_TOTAL": 10,       
    
    # Weighting: 70% Leakage Penalty, 30% Efficiency Penalty
    "DMS_ALPHA": 0.7,         
    
    # Rate Limit Protection: 
    # Groq Free Tier is ~30 requests/min. 
    # 2.5s sleep ensures we stay safe (approx 24 RPM).
    "SLEEP_BETWEEN_TURNS": 4.5 
}
