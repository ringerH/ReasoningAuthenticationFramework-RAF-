# src/iccr/metrics.py

def calculate_dms(query_trace: list, irrelevant_indices: list, budget: int, alpha: float = 0.7):
    """
    DMS = 1 - (Alpha * Leakage + (1-Alpha) * Inefficiency)
    """
    # 1. Identify what indices were accessed
    accessed_indices = set()
    for q in query_trace:
        if q.startswith("get_operand:"):
            try:
                idx = int(q.split(":")[1])
                accessed_indices.add(idx)
            except: pass

    # 2. Leakage (Lambda): Fraction of irrelevant set accessed
    if not irrelevant_indices:
        lambda_val = 0.0
    else:
        leaks = accessed_indices.intersection(set(irrelevant_indices))
        lambda_val = len(leaks) / len(irrelevant_indices)

    # 3. Inefficiency (Epsilon): Budget used
    epsilon_val = min(1.0, len(query_trace) / budget)

    # 4. Final Score
    dms = 1.0 - ((alpha * lambda_val) + ((1.0 - alpha) * epsilon_val))
    return max(0.0, dms)