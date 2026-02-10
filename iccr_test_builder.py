import os
import json
import sys

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.config import ICCR_CONFIG, ICCR_DATA_DIR
from src.generation.iccr_problem_generator import generate_type_a, generate_type_b, generate_type_c

def build_benchmark():
    print(f"--- [Builder] Generating 30-40-30 Split in {ICCR_DATA_DIR} ---")
    
    total = ICCR_CONFIG.get("BENCHMARK_SIZE", 30)
    
    # Calculate Split
    count_a = int(total * 0.3)
    count_b = int(total * 0.4)
    count_c = int(total * 0.3)
    
    # Adjust for rounding errors to ensure exact match
    current_sum = count_a + count_b + count_c
    if current_sum < total:
        count_b += (total - current_sum)
    
    print(f"Target Distribution: Type A={count_a}, Type B={count_b}, Type C={count_c}")
    
    os.makedirs(ICCR_DATA_DIR, exist_ok=True)
    
    # Helper to write files
    def write_set(filename, count, generator_func):
        path = os.path.join(ICCR_DATA_DIR, filename)
        with open(path, 'w', encoding='utf-8') as f:
            for _ in range(count):
                f.write(json.dumps(generator_func()) + "\n")
        print(f"✅ Generated {count} problems in {filename}")

    # 1. Generate Type A (Global Traps)
    write_set("test_type_a_global.jsonl", count_a, generate_type_a)
    
    # 2. Generate Type B (Partial Traps)
    write_set("test_type_b_partial.jsonl", count_b, generate_type_b)
    
    # 3. Generate Type C (Controls)
    write_set("test_type_c_control.jsonl", count_c, generate_type_c)
            
    print("\n--- [Builder] Complete. Ready for Testing. ---")

if __name__ == "__main__":
    build_benchmark()