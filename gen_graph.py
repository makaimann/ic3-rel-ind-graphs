#!/usr/bin/env python3
import argparse
from cnf_utils import read_cnf, assert_clauses, check_inductiveness, identify_invariants, Clause
from collections import deque
from graphviz import Digraph
from itertools import chain
from marco import SubsetSolver, MapSolver, enumerate_sets
import sys
from z3 import Solver, Not, And, sat, unsat, Implies, Bool

# This uses the z3 marco.py example
# I was using it incorrectly because it assumed that SubsetSolvers were only instantiated once
# That has been changed in the local version of marco.py
# but I also just implemented shrink directly in get_mus below
# def get_mus_marco(csolver):
#     '''
#     Returns a single MUS
#     '''
#     seed = set(range(csolver.n))
#     assert not csolver.check_subset(seed), "Expecting unsat"
#     MUS = csolver.shrink(seed)
#     return csolver.to_c_lits(MUS)

# def get_deps_marco(constraints, npinv):
#     constraints = constraints[:]
#     constraints.append(npinv)
#     csolver = SubsetSolver(constraints)
#     l2c = csolver.get_lit_constraint_map()

#     deps = set()
#     for l in get_mus_marco(csolver):
#         c = l2c[l]
#         if c.get_id() != npinv.get_id():
#             deps.add(Clause(c))
#     return deps

def get_mus(constraints):
    '''
    Returns a single MUS
    '''
    seed = set(range(len(constraints)))
    idx2indicator = {i:Bool(str(i)) for i in seed}
    indicator2idx = {b.get_id():i for (i,b) in idx2indicator.items()}

    s = Solver()
    for i, b in idx2indicator.items():
        s.add(Implies(b, constraints[i]))

    def check_subset(current_seed):
        assumptions = [idx2indicator[i] for i in current_seed]
        return (s.check(assumptions) == sat)

    current = set(seed)
    for i in seed:
        if i not in current:
            continue
        current.remove(i)
        if not check_subset(current):
            core = s.unsat_core()
            # TODO: do constraints never show up in the core? Seems like we could get a key error
            current = set(indicator2idx[ind.get_id()] for ind in core)
        else:
            current.add(i)
    return [constraints[i] for i in current]

def get_deps(constraints, npinv):
    constraints = constraints[:]
    constraints.append(npinv)
    # csolver = SubsetSolver(constraints)
    # l2c = csolver.get_lit_constraint_map()

    deps = set()
    for c in get_mus(constraints):
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

def debug_printing(inv2pinv, trans, prop, include_mapping=True):
    print('+++++++++++++++++++++++ debug printing +++++++++++++++++++++++++++')
    print('trans id =', trans._id)
    print('prop id =', prop._id)
    print('inv --> primed inv')
    if include_mapping:
        for inv, pinv in inv2pinv.items():
            print("{} --> {}".format(inv._id, pinv._id))
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

    z3trans = And([c._expr for c in trans])
    clause_trans = Clause(z3trans)

    # sanity check
    ssanity = Solver()
    ssanity.add(z3trans)
    for inv in inv_cand:
        ssanity.add(inv._expr)
    for pinv in inv_primed_cand[1:]:
        ssanity.add(pinv._expr)
    ssanity.add(Not(primeprop._expr))
    res = ssanity.check()
    assert res == unsat, "Expecting unsat but got {}".format(res)
    # end sanity check

    inv2pinv = identify_invariants(trans, inv_cand, inv_primed_cand)
    assert prop in inv2pinv

    invs = inv2pinv.keys()
    pinvs = inv2pinv.values()

    print("Finding dependencies...")

    constraints = [z3trans]
    for inv in invs:
        constraints.append(inv._expr)

    ind_solver = Solver()
    ind_solver.add(z3trans)

#    debug_printing(inv2pinv, clause_trans, prop, include_mapping=False)

    deps = {}
    to_visit = deque([prop])
    visited = set()
    count = 0
    while to_visit:
        if count % 20 == 0:
            print('#', end='')
            sys.stdout.flush()

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
