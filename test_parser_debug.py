# test_parser_debug.py

import json
import sys
sys.path.insert(0, '.')

from src.evaluation.response_parser import parse_response

# Load your latest results
results_file = "data/results/run_20251203_164325.jsonl"  # Replace with actual file

null_cases = []
incorrect_cases = []

with open(results_file, 'r') as f:
    for line in f:
        entry = json.loads(line)
        
        if entry.get('model_answer') is None and entry.get('raw_response'):
            null_cases.append({
                'problem': entry['problem'],
                'truth': entry['ground_truth'],
                'raw': entry['raw_response'][:200]  # First 200 chars
            })
        
        elif not entry.get('is_correct') and entry.get('model_answer') is not None:
            incorrect_cases.append({
                'problem': entry['problem'],
                'truth': entry['ground_truth'],
                'model': entry['model_answer'],
                'raw': entry['raw_response'][:200]
            })

print("="*60)
print("NULL RESPONSE CASES (Parser Failed)")
print("="*60)
for i, case in enumerate(null_cases[:5], 1):  # Show first 5
    print(f"\n[{i}] Problem: {case['problem']}")
    print(f"    Truth: {case['truth']}")
    print(f"    Raw: {case['raw']}...")
    print()

print("="*60)
print("INCORRECT ANSWER CASES")
print("="*60)
for i, case in enumerate(incorrect_cases[:5], 1):
    print(f"\n[{i}] Problem: {case['problem']}")
    print(f"    Truth: {case['truth']}")
    print(f"    Model: {case['model']}")
    print(f"    Raw: {case['raw']}...")
    print()