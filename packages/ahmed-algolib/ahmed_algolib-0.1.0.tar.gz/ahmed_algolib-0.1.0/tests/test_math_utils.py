import algolib
from algolib import gcd, lcm

def test_gcd_lcm():
    assert gcd(12, 18) == 6
    assert lcm(3, 5) == 15
    assert lcm(0, 5) == 0
