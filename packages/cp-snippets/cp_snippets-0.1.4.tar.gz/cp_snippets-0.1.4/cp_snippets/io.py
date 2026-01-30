import sys
input = sys.stdin.readline


def int_input():
    """Reads a single integer from standard input."""
    return int(input())


def str_input():
    """Reads a single line of string from standard input, stripping leading/trailing whitespace."""
    return input().strip()


def list_input(dtype=int):
    """Reads a line of space-separated values and returns a list. Default element type is int."""
    return list(map(dtype, input().split()))


def multi_input(dtype=int):
    """
    Reads a line of space-separated values and returns a map object.
    Usage: a, b, c = multi_input()
    """
    return map(dtype, input().split())


def matrix_input(n, m=None, dtype=int):
    """
    Reads a matrix of size n x m.
    If m is None, reads n lines where each line can have arbitrary number of elements.
    """
    if m is None:
        return [list(map(dtype, input().split())) for _ in range(n)]
    return [list(map(dtype, input().split()))[:m] for _ in range(n)]


def char_matrix(n):
    """Reads n lines of strings and converts them into a list of list of characters."""
    return [list(input().strip()) for _ in range(n)]


def read_all():
    """Reads all input from stdin until EOF and returns a list of tokens."""
    return sys.stdin.read().split()


def print_list(arr, sep=' '):
    """Prints elements of a list separated by 'sep'."""
    sys.stdout.write(sep.join(map(str, arr)) + '\n')


def print_yes_no(cond):
    """Prints 'YES' if cond is True, else 'NO'."""
    sys.stdout.write("YES\n" if cond else "NO\n")


def fast_reader():
    """Returns an iterator that yields tokens from stdin one by one."""
    return iter(sys.stdin.read().split())