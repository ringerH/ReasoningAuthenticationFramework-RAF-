import random
import operator
from typing import Tuple, Union, Callable

OPERATORS: list[Tuple[str, Callable]] = [
    ("+", operator.add),
    ("-", operator.sub),
    ("*", operator.mul),
    ("/", operator.truediv),
]

OPERAND_MIN = 1
OPERAND_MAX = 10


def _get_random_operand() -> int:
    """Returns a random integer from the defined range."""
    return random.randint(OPERAND_MIN, OPERAND_MAX)


def _build_expression(
    current_depth: int, max_depth: int
) -> Union[int, tuple]:
    
    
    if current_depth == max_depth:
        return _get_random_operand()

    op_str, op_func = random.choice(OPERATORS)

    left = _build_expression(current_depth + 1, max_depth)
    right = _build_expression(current_depth + 1, max_depth)

    # --- Robustness Check ---
    # Ensure no division by zero.
    # We must evaluate the 'right' branch *if* it's a tuple.
    if op_str == "/":
        right_val = _evaluate_expression(right)
        
        # If it's zero, regenerate the right branch until it's not.
        while abs(right_val) < 1e-9: # Check if close to zero
            right = _build_expression(current_depth + 1, max_depth)
            right_val = _evaluate_expression(right)

    return (left, op_func, right)


def _format_expression_str(expression: Union[int, tuple]) -> str:
    """
    Recursively formats the nested tuple into a human-readable string.
    
    e.g., ((5, <built-in function add>, 3), <built-in function mul>, 4)
    becomes "((5 + 3) * 4)"
    
    Note: This function adds parentheses around every operation to ensure
    the order of operations is unambiguous for the LLM.
    """
    # Base case: It's just a number
    if isinstance(expression, int):
        return str(expression)

    # Recursive step: Format the (left, op, right) tuple
    left, op_func, right = expression
    
    # Find the string for the operator function
    op_str = [s for s, f in OPERATORS if f == op_func][0]

    left_str = _format_expression_str(left)
    right_str = _format_expression_str(right)

    return f"({left_str} {op_str} {right_str})"


def _evaluate_expression(expression: Union[int, tuple]) -> float:
    """
    Recursively evaluates the nested tuple to get the correct answer.
    
    e.g., ((5, <built-in function add>, 3), <built-in function mul>, 4)
    evaluates to 32.0
    """
    # Base case: It's just a number
    if isinstance(expression, int):
        return float(expression)

    # Recursive step: Evaluate the (left, op, right) tuple
    left, op_func, right = expression

    left_val = _evaluate_expression(left)
    right_val = _evaluate_expression(right)

    return op_func(left_val, right_val)


# --- Public API Function ---

def generate_problem(depth: int) -> Tuple[str, float]:
    """
    Generates a single arithmetic problem for the complexity ladder.

    This is the main public-facing function for this module.

    Args:
        depth: The compositional depth of the expression.
               depth=0 -> "5"
               depth=1 -> "(2 + 3)"
               depth=2 -> "((4 * 1) + 5)"

    Returns:
        A tuple containing:
        1. The problem as a string (e.g., "((7 - 2) * 3)").
        2. The correct answer as a float (e.g., 15.0).
    """
    if depth < 0:
        raise ValueError("Depth cannot be negative")

    if depth == 0:
        # Special case: depth 0 is just a number
        operand = _get_random_operand()
        return str(operand), float(operand)

    # Our recursive builder considers depth 1 to have 1 operation.
    expr_tuple = _build_expression(current_depth=1, max_depth=depth)

    problem_str = _format_expression_str(expr_tuple)
    correct_answer = _evaluate_expression(expr_tuple)

    # Format answer to a reasonable precision
    if not correct_answer.is_integer():
        correct_answer = round(correct_answer, 4)

    return problem_str, correct_answer


# --- Self-Test Block ---

if __name__ == "__main__":
    """
    Run a simple test to demonstrate the module's functionality.
    This allows the script to be run directly for verification.
    
    To run: python src/generation/problem_generator.py
    """
    
    print("--- Problem Generator Self-Test ---")
    
    for d in range(5):
        problem, answer = generate_problem(d)
        print(f"Depth {d}: {problem} (Answer: {answer})")
    
    print("\n--- Test Complete ---")