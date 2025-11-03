import re
from typing import Optional

def parse_response(raw_text: str) -> Optional[float]:
    if not raw_text:
        return None
    
    # Priority 1: "Answer: X" pattern
    match = re.search(r"Answer:\s*([-+]?\d*\.?\d+)", raw_text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    
    # Priority 2: Last "= X" at end of line
    match = re.search(r"=\s*([-+]?\d*\.?\d+)\s*$", raw_text, re.MULTILINE)
    if match:
        return float(match.group(1))
    
    # Priority 3: Last number (fallback)
    numbers = re.findall(r"[-+]?\d*\.?\d+", raw_text)
    if numbers:
        return float(numbers[-1])
    
    return None


if __name__ == "__main__":
   
    
    print("Response Parser Self-Test")
    
    # Test case 1: User's example with chain-of-thought
    test_1 = """
    To evaluate the expression ((2 + 3) * 4) / 3, we need to follow the order of operations (PEMDAS):
    1. Evaluate the expression inside the parentheses: (2 + 3) = 5
    2. Multiply 5 by 4: 5 * 20
    3. Divide 20 by 3: 20 / 3 = 6.67
    So, the final result is 6.67.
    """
    
    # Test case 2: Simple answer
    test_2 = "The answer is 20."
    
    # Test case 3: No numbers
    test_3 = "I am not sure."
    
    # Test case 4: Negative number
    test_4 = "The result is -10.5."

    tests = {
        "CoT Example": (test_1, 6.67),
        "Simple Answer": (test_2, 20.0),
        "No Number": (test_3, None),
        "Negative Float": (test_4, -10.5)
    }

    all_passed = True
    for name, (text, expected) in tests.items():
        result = parse_response(text)
        is_correct = (result == expected)
        if not is_correct:
            all_passed = False
            
        print(f"Test: {name:<15} | Status: {'PASS' if is_correct else 'FAIL'}")
        print(f"  Input: \"{text.strip()[:40]}...\"")
        print(f"  Expected: {expected} | Got: {result}")
        print("-" * 20)

    print(f"\nOverall Result: {'All tests passed!' if all_passed else 'Some tests failed.'}")
    print("Test Complete")