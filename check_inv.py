#!/usr/bin/env python3
import argparse
from z3 import Solver, Not, And, Or, sat, unsat, Implies, Bool, substitute

from cnf_utils import read_cnf, get_lit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check invariant on a transition system")
    parser.add_argument("--init", type=str, help='Path to CNF file for initial states')
    parser.add_argument("--trans", type=str, help='Path to CNF file for transition relation')
    parser.add_argument("--inv", type=str, help='Path to CNF file for invariant')
    parser.add_argument("--primes", type=str, help='Path to space delimited mapping file')

    args = parser.parse_args()
    file_prime = args.primes

    init  = And([c._expr for c in read_cnf(args.init)])
    trans = And([c._expr for c in read_cnf(args.trans)])
    invl  = read_cnf(args.inv)
    assert invl
    prop  = invl[0]
    inv   = And([c._expr for c in invl])

    prime_mapping = []
    for line in open(file_prime, "r").read().splitlines():
        k, v = line.split()
        prime_mapping.append((get_lit(k), get_lit(v)))


    s = Solver()
    # IMPORTANT invariant of IC3ref
    # -1 (actually stored as -0 internally)
    # just used as "true"
    s.add(get_lit('-1'))

    init = And(init, prop._expr)

    print("init -> inv...", end='')
    query = And(init, Not(inv))
    s.push()
    s.add(query)
    print('OK' if s.check() == unsat else 'FAIL')
    s.pop()

    s.push()
    print('inv /\ T |= inv...', end='')
    s.add(And(inv, trans, Not(substitute(inv, prime_mapping))))
    print('OK' if s.check() == unsat else 'FAIL')
    s.pop()
