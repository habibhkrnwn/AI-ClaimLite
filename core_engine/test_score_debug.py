"""
Debug matching logic
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from services.consistency_service import calculate_match_score

# Test the scoring function directly
expected = ['87.44', '90.43', '90.59', '89.26', '92.11']
actual = ['87.44', '90.43', '90.59', '89.26', '92.11']

print(f"Expected: {expected}")
print(f"Actual: {actual}")

score, matched, total = calculate_match_score(expected, actual)

print(f"\nScore: {score}")
print(f"Matched: {matched}")
print(f"Total: {total}")
print(f"Should be: 5/5 = 1.0")
