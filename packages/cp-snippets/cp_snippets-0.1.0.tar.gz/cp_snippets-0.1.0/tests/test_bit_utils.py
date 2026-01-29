import unittest
import sys
import os

# Add the project root to sys.path so we can import pycp
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pycp.bit_utils import (
    set_bit, clear_bit, toggle_bit, check_bit, count_set_bits, lowest_set_bit, is_power_of_two
)

class TestBitUtils(unittest.TestCase):
    def test_set_bit(self):
        self.assertEqual(set_bit(0, 0), 1)
        self.assertEqual(set_bit(0, 2), 4)
        self.assertEqual(set_bit(4, 0), 5)
        self.assertEqual(set_bit(4, 2), 4)

    def test_clear_bit(self):
        self.assertEqual(clear_bit(7, 0), 6)
        self.assertEqual(clear_bit(7, 1), 5)
        self.assertEqual(clear_bit(4, 2), 0)
        self.assertEqual(clear_bit(4, 0), 4)

    def test_toggle_bit(self):
        self.assertEqual(toggle_bit(0, 0), 1)
        self.assertEqual(toggle_bit(1, 0), 0)
        self.assertEqual(toggle_bit(5, 1), 7)
        self.assertEqual(toggle_bit(7, 1), 5)

    def test_check_bit(self):
        self.assertTrue(check_bit(5, 0))  # 101 -> 0th bit is 1
        self.assertFalse(check_bit(5, 1)) # 101 -> 1st bit is 0
        self.assertTrue(check_bit(5, 2))  # 101 -> 2nd bit is 1

    def test_count_set_bits(self):
        self.assertEqual(count_set_bits(0), 0)
        self.assertEqual(count_set_bits(1), 1)
        self.assertEqual(count_set_bits(7), 3)
        self.assertEqual(count_set_bits(12345), bin(12345).count('1'))

    def test_lowest_set_bit(self):
        self.assertEqual(lowest_set_bit(12), 4) # 1100 -> 100 which is 4
        self.assertEqual(lowest_set_bit(6), 2)  # 110 -> 10 which is 2
        self.assertEqual(lowest_set_bit(1), 1)
        self.assertEqual(lowest_set_bit(0), 0)

    def test_is_power_of_two(self):
        self.assertTrue(is_power_of_two(1))
        self.assertTrue(is_power_of_two(2))
        self.assertTrue(is_power_of_two(4))
        self.assertTrue(is_power_of_two(1024))
        self.assertFalse(is_power_of_two(0))
        self.assertFalse(is_power_of_two(3))
        self.assertFalse(is_power_of_two(6))

if __name__ == '__main__':
    unittest.main()
