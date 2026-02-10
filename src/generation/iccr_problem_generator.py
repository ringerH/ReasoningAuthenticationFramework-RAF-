import random
from typing import Dict, Any

# --- TYPE A: GLOBAL TRAP (30%) ---
# Structure: (A + B - C) * 0
# Logic: 0 invalidates everything inside the parenthesis.
def generate_type_a() -> Dict[str, Any]:
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    c = random.randint(1, 10)
    
    return {
        "id": f"type_a_{random.randint(10000,99999)}",
        "problem_type": "type_a_global_trap",
        "expression_hidden": f"({a} + {b} - {c}) * 0",
        "structure_masked": "( ? + ? - ? ) * ?",
        "operands": [a, b, c, 0],
        "ground_truth": 0,
        "irrelevant_indices": [0, 1, 2], # A, B, C are irrelevant
        "critical_indices": [3]          # Only the 0 is critical
    }

# --- TYPE B: PARTIAL TRAP (40%) ---
# Structure: ((A * B) * 0) + C
# Logic: The inner chunk is dead (because of 0), but C is alive.
def generate_type_b() -> Dict[str, Any]:
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    c = random.randint(1, 50)
    
    return {
        "id": f"type_b_{random.randint(10000,99999)}",
        "problem_type": "type_b_partial_trap",
        "expression_hidden": f"(({a} * {b}) * 0) + {c}",
        "structure_masked": "(( ? * ? ) * ? ) + ?",
        "operands": [a, b, 0, c],
        "ground_truth": c,            # The result is just C
        "irrelevant_indices": [0, 1], # A and B are killed by 0
        "critical_indices": [2, 3]    # 0 and C are critical
    }

# --- TYPE C: CONTROL (30%) ---
# Structure: (A + B) * C
# Logic: Normal math. Everything is relevant.
def generate_type_c() -> Dict[str, Any]:
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    c = random.randint(2, 5) # Keep multiplier small to avoid huge numbers
    
    return {
        "id": f"type_c_{random.randint(10000,99999)}",
        "problem_type": "type_c_control",
        "expression_hidden": f"({a} + {b}) * {c}",
        "structure_masked": "( ? + ? ) * ?",
        "operands": [a, b, c],
        "ground_truth": (a + b) * c,
        "irrelevant_indices": [],     
        "critical_indices": [0, 1, 2] 
    }