from typing import List, Tuple

def compute_pi(s: str) -> List[int]:
    """
    Computes the prefix function (pi array) for KMP algorithm.
    pi[i] is the length of the longest proper prefix of s[0...i] 
    that is also a suffix of s[0...i].
    """
    m = len(s)
    pi = [0] * m
    for i in range(1, m):
        j = pi[i - 1]
        while j > 0 and s[i] != s[j]:
            j = pi[j - 1]
        if s[i] == s[j]:
            j += 1
        pi[i] = j
    return pi


def kmp_search(text: str, pattern: str) -> List[int]:
    """
    Finds all occurrences of pattern in text using KMP algorithm.
    Returns a list of starting indices (0-based).
    """
    if not pattern:
        return []
        
    pi = compute_pi(pattern)
    n, m = len(text), len(pattern)
    matches = []
    j = 0  # index for pattern
    
    for i in range(n):
        while j > 0 and text[i] != pattern[j]:
            j = pi[j - 1]
        if text[i] == pattern[j]:
            j += 1
        if j == m:
            matches.append(i - m + 1)
            j = pi[j - 1]
            
    return matches


def z_function(s: str) -> List[int]:
    """
    Computes the Z-function for string s.
    z[i] is the length of the longest common prefix between s and the suffix of s starting at i.
    """
    n = len(s)
    z = [0] * n
    l, r = 0, 0
    for i in range(1, n):
        if i <= r:
            z[i] = min(r - i + 1, z[i - l])
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if i + z[i] - 1 > r:
            l, r = i, i + z[i] - 1
    return z


class RollingHash:
    """
    Double rolling hash implementation for string matching and hashing.
    1-based indexing for hash queries is often easier, but we stick to 0-based for consistency with Python.
    """
    def __init__(self, s: str, base1: int = 313, mod1: int = 10**9 + 7, base2: int = 317, mod2: int = 10**9 + 9):
        self.mod1 = mod1
        self.mod2 = mod2
        self.base1 = base1
        self.base2 = base2
        n = len(s)
        
        self.hash1 = [0] * (n + 1)
        self.hash2 = [0] * (n + 1)
        self.pow1 = [1] * (n + 1)
        self.pow2 = [1] * (n + 1)
        
        for i in range(n):
            self.hash1[i + 1] = (self.hash1[i] * base1 + ord(s[i])) % mod1
            self.hash2[i + 1] = (self.hash2[i] * base2 + ord(s[i])) % mod2
            self.pow1[i + 1] = (self.pow1[i] * base1) % mod1
            self.pow2[i + 1] = (self.pow2[i] * base2) % mod2

    def get_hash(self, l: int, r: int) -> Tuple[int, int]:
        """
        Returns the double hash of substring s[l...r] (inclusive).
        """
        # hash[r+1] - hash[l] * base^(r-l+1)
        h1 = (self.hash1[r + 1] - self.hash1[l] * self.pow1[r - l + 1]) % self.mod1
        h2 = (self.hash2[r + 1] - self.hash2[l] * self.pow2[r - l + 1]) % self.mod2
        return (h1, h2)


def is_palindrome(s: str) -> bool:
    """Checks if the string s is a palindrome."""
    return s == s[::-1]


def manacher(s: str) -> List[int]:
    """
    Computes Manacher's algorithm to find longest palindromic substring.
    Returns the P array where P[i] is the length of the palindrome radius centered at T[i].
    The input string s is transformed to T = #s[0]#s[1]...#s[n-1]# to handle even length palindromes.
    The length of the palindrome centered at original index i (mapped to T) is P[2*i + 2] - 1.
    """
    if not s:
        return []
        
    t = '#'.join('^{}$'.format(s))
    n = len(t)
    P = [0] * n
    C = 0
    R = 0
    
    for i in range(1, n - 1):
        P[i] = (R > i) and min(R - i, P[2 * C - i]) # equals to min(R - i, P_mirror)
        
        # Attempt to expand palindrome centered at i
        while t[i + 1 + P[i]] == t[i - 1 - P[i]]:
            P[i] += 1
            
        # If palindrome centered at i expands past R,
        # adjust center based on expanded palindrome.
        if i + P[i] > R:
            C = i
            R = i + P[i]
    
    # Extract just the radius values for the transformed string
    # We strip the first and last sentinel characters ^ and $ which are not part of original analysis
    # t = ^ # a # b # a # $
    # indices: 0 1 2 3 4 5 6 7 8 
    # s = aba
    # Real useful part is from index 2 to n-2. 
    # But usually standard manacher return is the P array for the T string.
    # To conform to standard competitive programming templates, we return the full P array for T.
    # T here includes ^ and $ which simplifies boundary checks.
    
    return P
