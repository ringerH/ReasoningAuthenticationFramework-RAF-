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


def _build_expression(current_depth: int, max_depth: int) -> Union[int, tuple]:
    """
    Recursively builds an expression tree.
    - If we've reached max_depth, return a leaf (number)
    - Otherwise, create a binary operation with two sub-expressions
    """
    if current_depth >= max_depth:
        return _get_random_operand()

    op_str, op_func = random.choice(OPERATORS)

    left = _build_expression(current_depth + 1, max_depth)
    right = _build_expression(current_depth + 1, max_depth)

    # Avoid division by zero
    if op_str == "/":
        right_val = _evaluate_expression(right)
        retries = 0
        while abs(right_val) < 1e-9 and retries < 100:
            right = _build_expression(current_depth + 1, max_depth)
            right_val = _evaluate_expression(right)
            retries += 1
        if retries >= 100:
            op_str, op_func = ("*", operator.mul)

    return (left, op_func, right)


def _format_expression_str(expression: Union[int, tuple]) -> str:
    """Format the expression tree as a string with parentheses."""
    if isinstance(expression, int):
        return str(expression)

    left, op_func, right = expression
    
    # Find the string for the operator function
    op_str = [s for s, f in OPERATORS if f == op_func][0]

    left_str = _format_expression_str(left)
    right_str = _format_expression_str(right)

    return f"({left_str} {op_str} {right_str})"


def _evaluate_expression(expression: Union[int, tuple]) -> float:
    """Recursively evaluate the expression tree."""
    if isinstance(expression, int):
        return float(expression)

    left, op_func, right = expression

    left_val = _evaluate_expression(left)
    right_val = _evaluate_expression(right)

    return op_func(left_val, right_val)


def generate_problem(depth: int) -> Tuple[str, float]:
    """
    Generate a problem at the specified depth level.
    
    Depth interpretation:
    - Depth 0: Single operation like (2 + 3)
    - Depth 1: Nested once like ((2 + 3) * 4)
    - Depth 2: Nested twice like (((2 + 3) * 4) / 2)
    - And so on...
    """
    if depth < 0:
        raise ValueError("Depth cannot be negative")

    # Build expression tree starting from depth 0 up to the target depth
    expr_tuple = _build_expression(current_depth=0, max_depth=depth)

    problem_str = _format_expression_str(expr_tuple)
    correct_answer = _evaluate_expression(expr_tuple)

    # Format answer to a reasonable precision
    if not correct_answer.is_integer():
        correct_answer = round(correct_answer, 4)

    return problem_str, correct_answer


if __name__ == "__main__":
    print("--- Problem Generator Self-Test ---\n")
    
    for d in range(6):
        print(f"Depth {d} examples:")
        for i in range(3):
            problem, answer = generate_problem(d)
            print(f"  {i+1}. {problem} = {answer}")
        print()
    
    print("--- Test Complete ---")