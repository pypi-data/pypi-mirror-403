"""Prime-counting function

Counts the number of prime numbers less than or equal to an integer number.
"""
import argparse
from .sieve import sieve


def pi_function(n):
    return len(sieve(n))


def main():

    parser = argparse.ArgumentParser(prog='prime-counting',
                                     description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-n', '--limit',
                        dest='limit',
                        type=int,
                        default=100,
                        help='maximum integer up to which the prime numbers are counted. (default %(default)s)')

    args = parser.parse_args()

    pi = pi_function(args.limit)

    print(pi)


if __name__ == '__main__':
    main()

