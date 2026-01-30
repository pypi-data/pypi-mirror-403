def set_bit(n: int, i: int) -> int:
    """Sets the ith bit of n to 1."""
    return n | (1 << i)


def clear_bit(n: int, i: int) -> int:
    """Sets the ith bit of n to 0."""
    return n & ~(1 << i)


def toggle_bit(n: int, i: int) -> int:
    """Toggles the ith bit of n."""
    return n ^ (1 << i)


def check_bit(n: int, i: int) -> bool:
    """Checks if the ith bit of n is set."""
    return (n & (1 << i)) != 0


def count_set_bits(n: int) -> int:
    """Counts the number of set bits (1s) in the binary representation of n.
    
    Note: Requires Python 3.10+ for int.bit_count().
    """
    try:
        return n.bit_count()
    except AttributeError:
        return bin(n).count('1')


def lowest_set_bit(n: int) -> int:
    """Returns the value of the lowest set bit in n (e.g., for 12 (1100), returns 4 (0100))."""
    return n & -n


def is_power_of_two(n: int) -> bool:
    """Checks if n is a power of two."""
    return n > 0 and (n & (n - 1) == 0)
