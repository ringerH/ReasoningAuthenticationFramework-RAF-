import os
import sys
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.monitoring.logger import get_logger

def calculate_accuracies(results: List[Dict[str, Any]]) -> Dict[int, float]:
    """
    Calculates the final accuracy for each level.
    """
    logger = get_logger()
    logger.info(f"--- [Step 3: Calculate Per-Level Accuracy] ---")
    level_counts = {}
    level_correct = {}

    if not results:
         logger.warning("No results to calculate accuracy from.")
         return {}

    for res in results:
         
         if 'level' not in res or 'is_correct' not in res:
              logger.warning(f"Skipping invalid result entry: {res}")
              continue

         level = res['level']
         is_correct = res['is_correct']

         level_counts.setdefault(level, 0)
         level_correct.setdefault(level, 0)

         level_counts[level] += 1
         if is_correct:
             level_correct[level] += 1

    accuracies = {}
    if not level_counts:
        logger.warning("No valid levels found in results.")
        return {}

    
    min_level = min(level_counts.keys())
    max_level = max(level_counts.keys())

    for level in range(min_level, max_level + 1):
        count = level_counts.get(level, 0)
        correct = level_correct.get(level, 0)

        if count == 0:
            acc = 0.0
            # logger.info(f"  Level {level}: 0.00%  (0 / 0)") # Optionally log zero counts
        else:
            acc = (correct / count)
            logger.info(f"  Level {level}: {acc*100:.2f}%  ({correct} / {count})")

        accuracies[level] = acc

    return accuracies


def calculate_cds(accuracies: Dict[int, float]) -> float:
    """
    Calculates Accuracy Differences and final CDS.
    """
    logger = get_logger() # Get logger instance
    logger.info(f"--- [Step 4 & 5: Calculate CDS] ---")

    if not accuracies:
        logger.error("Accuracy data is empty. Cannot calculate CDS.")
        return 0.0

    sorted_levels = sorted(accuracies.keys())
    if not sorted_levels or sorted_levels[0] > 1:
        logger.warning(f"Accuracy data does not start near level 0 or 1 ({sorted_levels}). CDS might be less meaningful.")

    min_level_in_data = min(sorted_levels)
    max_level_in_data = max(sorted_levels)

    intended_max_D = 10 # Or MAX_DEPTH from config if imported
    D_to_use = max(intended_max_D, max_level_in_data) 

    if D_to_use < 1 : 
         logger.warning("Need levels up to at least 1 to calculate CDS.")
         return 0.0 

    total_drop = 0
    
    if 1 not in accuracies and 0 not in accuracies and D_to_use >=2 :
         logger.warning("Missing accuracy for level 1 (and 0), cannot calculate drop from L2 vs L1.")

    start_calc_level = 2 
    valid_drops_calculated = 0

    for d in range(start_calc_level, D_to_use + 1):
        if (d-1) not in accuracies:
            logger.warning(f"Missing accuracy for level {d-1}, cannot calculate drop for level {d}. Skipping.")
            continue 

        acc_d = accuracies.get(d, 0.0) 
        acc_d_minus_1 = accuracies.get(d-1, 0.0) 

        drop = abs(acc_d - acc_d_minus_1)
        logger.info(f"    - Drop (L{d} vs L{d-1}): |{acc_d*100:.2f}% - {acc_d_minus_1*100:.2f}%| = {drop*100:.2f}%")
        total_drop += drop
        valid_drops_calculated += 1

    if D_to_use == 0 or valid_drops_calculated == 0:
        logger.warning("Could not calculate any valid drops. Returning default CDS.")
        return 1.0

    avg_drop = total_drop / D_to_use
    cds_score = 1.0 - avg_drop

    logger.info(f"\n  Total Drop Sum: {total_drop*100:.2f}% (based on {valid_drops_calculated} differences)")
    logger.info(f"  Max Depth (D) used for avg: {D_to_use}")
    logger.info(f"  Average Drop (Total Drop / D): {avg_drop*100:.4f}%")

    cds_score = max(0.0, min(1.0, cds_score))

    return cds_score