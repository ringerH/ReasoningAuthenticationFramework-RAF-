import os
import json
import glob
import datetime
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.config import ICCR_CONFIG, ICCR_DATA_DIR, RESULTS_DIR
from src.iccr.evaluator import run_iccr_agent_loop
from src.iccr.metrics import calculate_dms
from src.monitoring.tracker import ResultTracker

def run_real_pipeline():
    print("Running ICCR Test")
    
    # 1. Setup Result Logger
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(RESULTS_DIR, f"iccr_run_{timestamp}.jsonl")
    
    tracker = ResultTracker(results_file)
    print(f"📋 Logging results to: {results_file}")

    # 2. Find Test Sets
    files = glob.glob(os.path.join(ICCR_DATA_DIR, "*.jsonl"))
    if not files:
        print(f"❌ ERROR: No data found in {ICCR_DATA_DIR}")
        return

    # 3. Process Each Test Set
    for filepath in files:
        filename = os.path.basename(filepath)
        print(f"\n📂 Processing Test Set: {filename}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            problems = [json.loads(line) for line in f]

        total_probs = len(problems)
        
        # Run loop
        for i, prob in enumerate(problems):
            print(f"\n🔹 Problem {i+1}/{total_probs} (ID: {prob.get('id', 'N/A')})")
            
            # A. Run Real Agent Loop
            result = run_iccr_agent_loop(prob, ICCR_CONFIG["BUDGET_TOTAL"])
            
            # B. Calculate Metric
            dms_score = calculate_dms(
                result['query_trace'], 
                prob['irrelevant_indices'], 
                ICCR_CONFIG["BUDGET_TOTAL"],
                ICCR_CONFIG["DMS_ALPHA"]
            )
            
            # C. Log to File (INCLUDING HISTORY)
            log_payload = {
                "trace": result['query_trace'],
                "dms_score": dms_score,
                "problem_type": prob['problem_type'],
                "full_history": result.get('full_history', [])  # <-- ADD THIS
            }
            
            tracker.log_result(
                level=0, 
                problem=prob['expression_hidden'],
                ground_truth=prob['ground_truth'],
                model_answer=result['model_answer'],
                is_correct=result['is_correct'],
                raw_response=json.dumps(log_payload)
            )
            
            # D. Console Feedback
            status_icon = "✅" if result['is_correct'] else "❌"
            privacy_icon = "🛡️" if dms_score > 0.8 else "⚠️"
            print(f"   {status_icon} Correct | {privacy_icon} DMS: {dms_score:.2f} | Trace: {len(result['query_trace'])} steps")

    print("\n========================================")
    print("--- ✅ BENCHMARK COMPLETE ---")
    print("========================================")

if __name__ == "__main__":
    run_real_pipeline()