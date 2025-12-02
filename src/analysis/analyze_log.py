# src/analysis/analyze_log.py

import re
import sys
import argparse
import numpy as np
from sklearn.metrics import auc

def parse_and_evaluate(log_filepath):
    """
    Parses a log file to extract Level/Accuracy pairs and calculates
    the Robust Compositional Decay Score (R-CDS).
    """
    print(f"--- Analyzing Log: {log_filepath} ---")
    
    try:
        with open(log_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {log_filepath}")
        return

    # 1. Regex to match lines like: "Level 0: 100.00%"
    # Captures: Level (group 1) and Percentage (group 2)
    pattern = re.compile(r"Level\s+(\d+):\s+(\d+\.?\d*)%")
    
    data_map = {}
    
    for line in content.splitlines():
        match = pattern.search(line)
        if match:
            level = int(match.group(1))
            acc_pct = float(match.group(2))
            # Store as decimal (0.0 - 1.0)
            data_map[level] = acc_pct / 100.0

    if not data_map:
        print("No accuracy data found. Ensure the log contains lines like 'Level X: Y%'.")
        return

    # Sort levels to ensure sequence (Level 0, 1, 2...)
    levels = sorted(data_map.keys())
    accuracies = [data_map[l] for l in levels]
    
    print(f"Found {len(levels)} levels: {dict(zip(levels, accuracies))}")
    print("-" * 40)

    # =========================================
    # METRIC 1: Old CDS (Average Drop)
    # =========================================
    drops = []
    for i in range(len(accuracies) - 1):
        # Drop = Previous - Current
        d = accuracies[i] - accuracies[i+1]
        drops.append(d)
    
    avg_drop = np.mean(drops) if drops else 0
    old_score = 1.0 - avg_drop

    # =========================================
    # METRIC 2: New Robust Score (Max-Drop Penalized AUC)
    # =========================================
    # A. Performance: Area Under Curve
    x = np.array(levels)
    y = np.array(accuracies)
    
    # Normalize AUC by the depth range (e.g. 5) to get 0-1
    if x[-1] - x[0] == 0:
        perf_auc = 0.0
    else:
        perf_auc = auc(x, y) / (x[-1] - x[0])
    
    # B. Stability: Find the "Cliff" (Max positive drop)
    valid_drops = [max(0, d) for d in drops]
    max_cliff = max(valid_drops) if valid_drops else 0.0
    
    # C. Penalty Calculation
    # We penalize the AUC by the size of the cliff.
    # If cliff is 0.5 (50% drop), penalty factor is 0.5.
    stability_factor = 1.0 - max_cliff
    robust_score = perf_auc * max(0, stability_factor)

    # =========================================
    # FINAL REPORT
    # =========================================
    print(f"\nMetric Comparison:")
    print(f"1. Standard CDS (Avg Drop):  {old_score:.4f}  (Often inflated)")
    print(f"2. Robust Score (Cliff Aware): {robust_score:.4f}  (Penalizes sudden failures)")
    
    print("-" * 40)
    if max_cliff > 0.40:
         print(f"[ALERT] CRITICAL FAILURE DETECTED")
         print(f"        A 'Cliff' of -{max_cliff*100:.1f}% was found.")
         print(f"        This indicates pattern matching failure rather than compositional decay.")
    else:
         print(f"[PASS] Decay appears gradual. No massive cliffs detected.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate Robust Decay metrics from a benchmark log.")
    parser.add_argument("logfile", help="Path to the .log file (e.g., logs/benchmark_xxx.log)")
    args = parser.parse_args()
    
    parse_and_evaluate(args.logfile)