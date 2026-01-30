def gcd(a, b):
    """Computes the Greatest Common Divisor of a and b."""
    while b:
        a, b = b, a % b
    return a


def lcm(a, b):
    """Computes the Least Common Multiple of a and b."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // gcd(a, b)


def mod_add(a, b, mod):
    """Computes (a + b) % mod."""
    return (a + b) % mod


def mod_mul(a, b, mod):
    """Computes (a * b) % mod."""
    return (a * b) % mod


def mod_pow(a, b, mod):
    """Computes (a^b) % mod using binary exponentiation."""
    res = 1
    a %= mod
    while b:
        if b & 1:
            res = res * a % mod
        a = a * a % mod
        b >>= 1
    return res


def mod_inv(a, mod):
    """
    Computes modular inverse of a modulo mod using Fermat's Little Theorem.
    Assumes mod is prime.
    """
    return mod_pow(a, mod - 2, mod)


def init_nCr(N, mod):
    """
    Precomputes factorials and inverse factorials up to N for nCr calculations.
    Returns: (fact, invfact) lists.
    """
    fact = [1] * (N + 1)
    invfact = [1] * (N + 1)

    for i in range(1, N + 1):
        fact[i] = fact[i - 1] * i % mod

    invfact[N] = mod_inv(fact[N], mod)
    for i in range(N, 0, -1):
        invfact[i - 1] = invfact[i] * i % mod

    return fact, invfact


def nCr(n, r, fact, invfact, mod):
    """
    Computes nCr % mod using precomputed factorials.
    Returns 0 if r < 0 or r > n.
    """
    if r < 0 or r > n:
        return 0
    return fact[n] * invfact[r] % mod * invfact[n - r] % mod


def sieve(n):
    """
    Sieve of Eratosthenes to find primes up to n.
    Returns: is_prime boolean list where is_prime[i] is True if i is prime.
    """
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False

    for i in range(2, int(n ** 0.5) + 1):
        if is_prime[i]:
            for j in range(i * i, n + 1, i):
                is_prime[j] = False

    return is_prime


def spf_sieve(n):
    """
    Computes Smallest Prime Factor (SPF) for each number up to n.
    Useful for fast prime factorization.
    """
    spf = list(range(n + 1))
    for i in range(2, int(n ** 0.5) + 1):
        if spf[i] == i:
            for j in range(i * i, n + 1, i):
                if spf[j] == j:
                    spf[j] = i
    return spf


def prime_factorize(x, spf):
    """
    Returns prime factorization of x using precomputed SPF array.
    Returns: Dictionary {prime_factor: exponent}.
    """
    factors = {}
    while x > 1:
        p = spf[x]
        factors[p] = factors.get(p, 0) + 1
        x //= p
    return factors


def euler_totient(n, spf):
    """
    Computes Euler's Totient function phi(n) using SPF.
    phi(n) = count of integers <= n coprime to n.
    """
    res = n
    while n > 1:
        p = spf[n]
        res -= res // p
        while n % p == 0:
            n //= p
    return res