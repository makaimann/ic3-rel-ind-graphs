#!/usr/bin/env python3
import argparse
from cnf_utils import read_cnf, assert_clauses, check_inductiveness, identify_invariants, Clause
from collections import deque
from graphviz import Digraph
from itertools import chain
from marco import SubsetSolver, MapSolver, enumerate_sets
import sys
from z3 import Solver, Not, And

def get_mus(csolver):
    '''
    Returns a single MUS
    '''
    seed = set(range(csolver.n))
    MUS = csolver.shrink(seed)
    return csolver.to_c_lits(MUS)

def get_deps(constraints, npinv):
    constraints = constraints[:]
    constraints.append(npinv)
    csolver = SubsetSolver(constraints)
    l2c = csolver.get_lit_constraint_map()

    deps = set()
    for l in get_mus(csolver):
        c = l2c[l]
        if c.get_id() != npinv.get_id():
            deps.add(Clause(c))
    return deps

def check_single_inv_induction(solver, inv, npinv):
    # assumes the transition relation has already been added
    solver.push()
    solver.add(inv)
    solver.add(npinv)
    # returns true if it IS inductive
    res = str(solver.check()) == "unsat"
    solver.pop()
    return res

def debug_printing(pinv2inv, trans, prop, include_mapping=True):
    print('+++++++++++++++++++++++ debug printing +++++++++++++++++++++++++++')
    print('trans id =', trans._id)
    print('prop id =', prop._id)
    print('inv --> primed inv')
    if include_mapping:
        for pinv, inv in pinv2inv.items():
            print("{} --> {}".format(inv._id, pinv._id))
    # print('----------------mucs------------------')
    # for oinv, deps in mucs:
    #     print("{}: {}".format(oinv._id, [d._id for d in deps]))
    print('+++++++++++++++++++++ end debug printing +++++++++++++++++++++++++')

def main():
    parser = argparse.ArgumentParser(description="Finds the induction "
                                     "graph for a proof of correctness "
                                     "produced by (a modified) IC3Ref")
    parser.add_argument('-t', dest="trans_filename",
                        metavar='<TRANS_FILE>',
                        help='The file with a CNF encoding of the transition relation')
    parser.add_argument('-i', dest='invcand_filename',
                        metavar='<INVCAND_FILE>',
                        help='CNF of candidate invariants from an IC3 frame')
    parser.add_argument('-ip', dest='invprime_cand_filename',
                        metavar='<INVPRIMECAND_FILENAME>',
                        help='primed CNF of candidate invaraiants from an IC3 frame')
    parser.add_argument('-o', dest='outname',
                        metavar='<OUTPUT_FILE>',
                        help='Filename to write the graphviz graph to.')
    args = parser.parse_args()
    trans = read_cnf(args.trans_filename)
    inv_cand = read_cnf(args.invcand_filename)
    inv_primed_cand = read_cnf(args.invprime_cand_filename)
    outname = args.outname

    # the first invariant is assumed to be the property
    # we don't want to remove that, so take it out now and add it back afterwards
    prop = inv_cand[0]
    primeprop = inv_primed_cand[0]
    pinv2inv = identify_invariants(trans, inv_cand[1:], inv_primed_cand[1:])
    pinv2inv[primeprop] = prop

    if len(pinv2inv) == 1:
        print("Zero invariants (other than property), aborting")
        sys.exit(0)

    invs = pinv2inv.values()
    pinvs = pinv2inv.keys()

    # look up the other way
    inv2pinv = {}
    for k, v in pinv2inv.items():
        inv2pinv[v] = k

    print("Finding dependencies...")

    z3trans = And([c._expr for c in trans])
    clause_trans = Clause(z3trans)
    neg_prime_inv_map = {}
    constraints = [z3trans]
    for inv in invs:
        constraints.append(inv._expr)

    ind_solver = Solver()
    ind_solver.add(z3trans)

#    debug_printing(pinv2inv, clause_trans, prop, include_mapping=False)

    deps = {}
    to_visit = deque([prop])
    visited = set()
    count = 0
    while to_visit:
        if count % 20 == 0:
            print('#', end='')

        inv = to_visit.pop()
        pinv = inv2pinv[inv]

#        print('visiting', inv._id, pinv._id)

        if inv in visited:
#            print('skipping because already in visited')
            continue
        else:
            visited.add(inv)
            invdeps = get_deps(constraints, Not(pinv._expr))
#            print("invdeps", [i._id for i in invdeps])
            for i in invdeps:
                if i != clause_trans:
                    to_visit.appendleft(i)
            deps[inv] = invdeps
            count += 1

    print('\nBuilding graph...')
    dot = Digraph(comment="Induction Graph")

    to_visit = deque()
    visited = set()
    # handle prop specially
    visited.add(prop)
    for d in deps[prop]:
        if d == prop:
            dot.edge('Prop', 'Prop')
        elif d != clause_trans:
            to_visit.appendleft(d)
            dot.edge('Prop', str(d._id))

    while to_visit:
        inv = to_visit.pop()
        if inv in visited:
            continue
        visited.add(inv)
        if inv not in deps:
            # inv is a leaf
            continue
        for d in deps[inv]:
            if d == prop:
                dot.edge(str(inv._id), 'Prop')
            elif d == clause_trans:
                continue
            else:
                dot.edge(str(inv._id), str(d._id))
                to_visit.appendleft(d)

    dot.render('./%s.dot'%outname)

    print('==================== completed ====================')


if __name__ == "__main__":
    main()
