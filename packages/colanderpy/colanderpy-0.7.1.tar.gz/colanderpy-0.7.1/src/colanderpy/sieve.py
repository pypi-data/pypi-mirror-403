"""The Sieve of Eratosthenes.

Returns the list of prime numbers up to a maximum integer.
"""
import argparse
import numpy as np

def sieve(n):
    """Sieve of Eratosthenes. Returns all prime numbers up to n"""
    if n < 2:
        return []
    # boolean sieve
    is_prime = np.full(n + 1, True, dtype=bool)
    # 0 and 1 are not considered prime numbers
    is_prime[0] = is_prime[1] = False
    # all even numbers are not prime numbers
    is_prime[np.arange(4, n+1, 2)] = False
    # loop on odd numbers
    up_to_n = np.sqrt(n)
    for p in np.arange(3, n+1, 2):
        if p > up_to_n:
            break
        is_prime[np.arange(p*p, n+1, 2*p)] = False
    return np.arange(n + 1)[is_prime]


def main():

    parser = argparse.ArgumentParser(prog='sieve',
                                     description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-n', '--limit',
                        dest='limit',
                        type=int,
                        default=100,
                        help='maximum integer up to which the prime numbers are searched. (default %(default)s)')

    args = parser.parse_args()

    n = sieve(args.limit)

    print(" ".join([str(i) for i in n]))


if __name__ == '__main__':
    main()

