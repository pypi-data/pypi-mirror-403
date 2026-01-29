import unittest
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pycp.strings import (
    compute_pi, kmp_search, z_function, RollingHash, is_palindrome, manacher
)

class TestStringUtils(unittest.TestCase):
    def test_kmp(self):
        text = "ABABDABACDABABCABAB"
        pattern = "ABABCABAB"
        # Matches at index 10
        self.assertEqual(kmp_search(text, pattern), [10])
        
        text2 = "AAAAA"
        pattern2 = "AA"
        # Matches at 0, 1, 2, 3
        self.assertEqual(kmp_search(text2, pattern2), [0, 1, 2, 3])
        
        self.assertEqual(kmp_search("ABC", "DEF"), [])
        self.assertEqual(compute_pi("ABABAC"), [0, 0, 1, 2, 3, 0])

    def test_z_function(self):
        s = "aabcaabxaaaz"
        # z array manually: 
        # a a b c a a b x a a a z
        # - 1 0 0 3 1 0 0 2 2 1 0 
        # Note: z[0] is usually 0 in standard implementations or undefined, our implementation might leave it as 0 or handle it.
        # Let's check a simpler one.
        s2 = "aaaaa"
        # z: 0 4 3 2 1
        self.assertEqual(z_function(s2), [0, 4, 3, 2, 1])
        
        s3 = "abacaba"
        # z: 0 0 1 0 3 0 1
        self.assertEqual(z_function(s3), [0, 0, 1, 0, 3, 0, 1])

    def test_rolling_hash(self):
        s = "abcdeabcde"
        rh = RollingHash(s)
        # abcde at 0 and abcde at 5 should match
        self.assertEqual(rh.get_hash(0, 4), rh.get_hash(5, 9))
        self.assertNotEqual(rh.get_hash(0, 4), rh.get_hash(0, 3))
        
        # Test collision resistance (basic)
        s2 = "ab"
        s3 = "ba"
        rh2 = RollingHash(s2)
        rh3 = RollingHash(s3)
        self.assertNotEqual(rh2.get_hash(0, 1), rh3.get_hash(0, 1))

    def test_is_palindrome(self):
        self.assertTrue(is_palindrome("aba"))
        self.assertTrue(is_palindrome("abba"))
        self.assertFalse(is_palindrome("abc"))
        self.assertTrue(is_palindrome("a"))
        self.assertTrue(is_palindrome(""))

    def test_manacher(self):
        s = "aba"
        # T = ^#a#b#a#$
        # P = 010131010 (approx, depends on implementation boundary)
        # Our implementation uses ^ and $ sentinels.
        # T: ^ # a # b # a # $
        # i: 0 1 2 3 4 5 6 7 8
        # P: 0 1 0 1 3 1 0 1 0
        p = manacher(s)
        self.assertEqual(p[4], 3) # Center at 'b' (#b#), radius 3 -> #a#b#a#
        
        s2 = "abba"
        # T: ^ # a # b # b # a # $
        # i: 0 1 2 3 4 5 6 7 8 9 10
        # P: 0 1 0 1 0 4 0 1 0 1 0 
        p2 = manacher(s2)
        self.assertEqual(p2[5], 4) # Center at '#' between b and b, radius 4 -> #a#b#b#a#

if __name__ == '__main__':
    unittest.main()
