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
    return random.randint(OPERAND_MIN, OPERAND_MAX)


def _build_expression(
    current_depth: int, max_depth: int
) -> Union[int, tuple]:
    
    
    if current_depth == max_depth:
        return _get_random_operand()

    op_str, op_func = random.choice(OPERATORS)

    left = _build_expression(current_depth + 1, max_depth)
    right = _build_expression(current_depth + 1, max_depth)

   
    if op_str == "/":
        right_val = _evaluate_expression(right)
        
        # If it's zero, regenerate the right branch until it's not.
        while abs(right_val) < 1e-9: # Check if close to zero
            right = _build_expression(current_depth + 1, max_depth)
            right_val = _evaluate_expression(right)

    return (left, op_func, right)


def _format_expression_str(expression: Union[int, tuple]) -> str:

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
    
    print("--- Problem Generator Self-Test ---")
    
    for d in range(5):
        problem, answer = generate_problem(d)
        print(f"Depth {d}: {problem} (Answer: {answer})")
    
    print("\n--- Test Complete ---")