#!/usr/bin/env python3
import argparse
from z3 import Solver, Not, And, Or, sat, unsat, Implies, Bool, substitute, ExprRef

from cnf_utils import read_cnf, get_lit

from typing import Set

def get_free_vars(e: ExprRef) -> Set[ExprRef]:
    free_vars = set()
    to_visit = [e]
    visited  = set()
    while to_visit:
        t = to_visit.pop()

        if t not in visited:
            visited.add(t)
            to_visit.append(t)
            for c in t.children():
                to_visit.append(c)

        elif not t.children():
            # assuming no children means it's a variable
            free_vars.add(t)

    return free_vars

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
    prop  = invl[0]._expr
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

    # add property to initial states
    # IC3ref omits this for some reason
    init = And(init, prop)

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

    s.push()
    print('inv -> prop...', end='')
    s.add(Not(Implies(inv, prop)))
    print('OK' if s.check() == unsat else 'FAIL')
    s.pop()

    free_vars = get_free_vars(inv)
    prime_mapping_ids = set(v0.get_id() for v0, v1 in prime_mapping)
    assert all(fv.get_id() in prime_mapping_ids for fv in free_vars), "expecting all current state variables"
