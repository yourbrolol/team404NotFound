from decimal import Decimal

# Case 1: int * Decimal
try:
    res = 100 * Decimal("1.00")
    print(f"int * Decimal: {res} (type: {type(res)})")
except TypeError as e:
    print(f"int * Decimal failed: {e}")

# Case 2: float * Decimal
try:
    res = 100.0 * Decimal("1.00")
    print(f"float * Decimal: {res} (type: {type(res)})")
except TypeError as e:
    print(f"float * Decimal failed: {e}")
