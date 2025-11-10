# src/analysis/reporting.py

import os
from typing import Dict
from src.monitoring.logger import get_logger

def log_final_report(
    accuracies: Dict[int, float], 
    cds_score: float, 
    results_filename: str, 
    benchmark_filename: str
):
    """Logs the final formatted report to the console."""
    
    logger = get_logger()
    
    logger.info("\n" + "="*30)
    logger.info("--- [FINAL BENCHMARK REPORT] ---")
    logger.info(f"Results file: {results_filename}")
    logger.info(f"Benchmark file used: {benchmark_filename}")
    logger.info("="*30)
    logger.info("\nPer-Level Accuracy:")

    if accuracies:
        all_levels = sorted(accuracies.keys())
        if all_levels:
            min_l, max_l = min(all_levels), max(all_levels)
            for level in range(min_l, max_l + 1):
                 acc = accuracies.get(level, 0.0)
                 logger.info(f"  Level {level}: {acc*100:.2f}%")
        else:
            logger.warning("Accuracy dictionary was empty.")
    else:
        logger.warning("No accuracy results to report.")

    if isinstance(cds_score, float):
         logger.info(f"\nCompositional Decay Score (CDS): {cds_score:.4f}")
    else:
         logger.warning("CDS score could not be calculated or was invalid.")

    logger.info("\n [Report Complete]")