import re
from typing import Optional

def parse_response(raw_text: str) -> Optional[float]:
    """
    Parses the raw text response from a model to find a numeric answer.

    It tries a "waterfall" of regex patterns in order of priority:
    1. FINAL_ANSWER: <fraction> (e.g., "FINAL_ANSWER: 41/9")
    2. FINAL_ANSWER: <number> (e.g., "FINAL_ANSWER: 4.55")
    3. Answer: <number> (e.g., "Answer: 20")
    4. = <number> (at the end of a line)
    5. Last number found in the string (fallback)
    """
    if not raw_text:
        return None

    # Priority 1 & 2: Look for "FINAL_ANSWER:" with support for fractions
    # This regex has two parts, separated by '|':
    # Part 1: `FINAL_ANSWER:\s*([-+]?\d*\.?\d+)\s*/\s*([-+]?\d*\.?\d+)`
    #   - Looks for "FINAL_ANSWER:", whitespace,
    #   - then captures a number (group 1, numerator),
    #   - then a "/", then captures another number (group 2, denominator).
    # Part 2: `FINAL_ANSWER:\s*([-+]?\d*\.?\d+)`
    #   - Looks for "FINAL_ANSWER:", whitespace,
    #   - then captures a single number (group 3).
    fraction_or_float_regex = (
        r"FINAL_ANSWER:\s*([-+]?\d*\.?\d+)\s*/\s*([-+]?\d*\.?\d+)"  # Priority 1 (Fraction)
        r"|"
        r"FINAL_ANSWER:\s*([-+]?\d*\.?\d+)"  # Priority 2 (Float/Int)
    )
    
    match = re.search(fraction_or_float_regex, raw_text, re.IGNORECASE)
    if match:
        if match.group(1) and match.group(2):  # Part 1 (Fraction) was matched
            try:
                numerator = float(match.group(1))
                denominator = float(match.group(2))
                if denominator == 0:
                    return None # Avoid division by zero
                return numerator / denominator
            except (ValueError, ZeroDivisionError):
                pass  # Fall through to other patterns if conversion fails
        
        elif match.group(3):  # Part 2 (Float/Int) was matched
            try:
                return float(match.group(3))
            except ValueError:
                pass  # Fall through

    # Priority 3: "Answer: X" pattern (Old Priority 1)
    match = re.search(r"Answer:\s*([-+]?\d*\.?\d+)", raw_text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    # Priority 4: Last "= X" at end of line (Old Priority 2)
    match = re.search(r"=\s*([-+]?\d*\.?\d+)\s*$", raw_text, re.MULTILINE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    # Priority 5: Last number (fallback) (Old Priority 3)
    numbers = re.findall(r"[-+]?\d*\.?\d+", raw_text)
    if numbers:
        try:
            return float(numbers[-1])
        except ValueError:
            pass

    return None


if __name__ == "__main__":
    """print(f"\nOverall Result: {'All tests passed!' if all_passed else 'Some tests failed.'}")
    print("--- [Test Complete] ---")
    """