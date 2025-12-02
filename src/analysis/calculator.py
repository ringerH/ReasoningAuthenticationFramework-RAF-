import os
import sys
import numpy as np
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.monitoring.logger import get_logger

def calculate_accuracies(results: List[Dict[str, Any]]) -> Dict[int, float]:
    """
    Calculates accuracy per complexity level (Ops count).
    """
    logger = get_logger()
    logger.info(f"--- [Step 3: Calculate Accuracy per Complexity Step] ---")
    
    level_counts = {}
    level_correct = {}

    if not results:
         return {}

    for res in results:
         if 'level' not in res or 'is_correct' not in res:
              continue
         level = res['level']
         is_correct = res['is_correct']
         level_counts[level] = level_counts.get(level, 0) + 1
         if is_correct:
             level_correct[level] = level_correct.get(level, 0) + 1

    accuracies = {}
    sorted_levels = sorted(level_counts.keys())

    for level in sorted_levels:
        count = level_counts[level]
        correct = level_correct.get(level, 0)
        acc = (correct / count) if count > 0 else 0.0
        logger.info(f"  Complexity {level} Ops: {acc*100:.2f}%  ({correct}/{count})")
        accuracies[level] = acc

    return accuracies

def calculate_cds(accuracies: Dict[int, float]) -> float:
    """
    Calculates Old CDS and New Robust Score.
    """
    logger = get_logger()
    logger.info(f"--- [Step 4: Calculate Decay Metrics] ---")

    if not accuracies:
        return 0.0

    levels = sorted(accuracies.keys())
    acc_values = [accuracies[l] for l in levels]

    # Calculate Drops
    drops = []
    for i in range(len(levels) - 1):
        d = acc_values[i] - acc_values[i+1]
        drops.append(d)
        if d > 0.4:
            logger.warning(f" CLIFF DETECTED: {levels[i]}->{levels[i+1]} ops (-{d*100:.1f}%)")

    # Old CDS
    avg_drop = np.mean(drops) if drops else 0.0
    cds_score = 1.0 - avg_drop

    # Robust Score
    valid_declines = [max(0, d) for d in drops]
    max_cliff = max(valid_declines) if valid_declines else 0.0
    perf_score = np.mean(acc_values)
    robust_score = perf_score * max(0, 1.0 - max_cliff)

    logger.info(f"  Standard CDS: {cds_score:.4f}")
    logger.info(f"  Robust Score: {robust_score:.4f}")
    
    return robust_score