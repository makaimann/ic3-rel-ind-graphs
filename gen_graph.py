#!/usr/bin/env python3
import argparse
from cnf_utils import read_cnf, assert_clauses, check_inductiveness, identify_invariants, Clause
from graphviz import Digraph
from itertools import chain
from marco import SubsetSolver, MapSolver, enumerate_sets
import sys
from z3 import Solver, Not, And

def get_mus(csolver, map_):
    '''
    Returns a single MUS
    '''
    seed = map_.next_seed()
    MUS = csolver.shrink(seed)
    return csolver.to_c_lits(MUS)

def get_deps(constraints, npinv):
    constraints = constraints[:]
    constraints.append(npinv)
    csolver = SubsetSolver(constraints)
    l2c = csolver.get_lit_constraint_map()
    msolver = MapSolver(n=csolver.n)

    deps = set()
    for l in get_mus(csolver, msolver):
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

def debug_printing(pinv2inv, mucs, trans):
    print('+++++++++++++++++++++++ debug printing +++++++++++++++++++++++++++')
    print('trans id =', trans._id)
    print('inv --> primed inv')
    for pinv, inv in pinv2inv.items():
        print("{} --> {}".format(inv._id, pinv._id))
    print('----------------mucs------------------')
    for oinv, deps in mucs:
        print("{}: {}".format(oinv._id, [d._id for d in deps]))
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

    pinv2inv = identify_invariants(trans, inv_cand, inv_primed_cand)

    if len(pinv2inv) == 0:
        print("Zero invariants, aborting")
        sys.exit(0)

    invs = pinv2inv.values()
    pinvs = pinv2inv.keys()
    s = Solver()
    assert_clauses(s, trans)
    print('Check inductiveness of invariants')
    assert check_inductiveness(s, pinv2inv)

    print("Running MARCO...")

    z3trans = And([c._expr for c in trans])

    clause_trans = Clause(z3trans)

    neg_prime_inv_map = {}

    constraints = [z3trans]
    for inv in invs:
        constraints.append(inv._expr)

    ind_solver = Solver()
    ind_solver.add(z3trans)

    mucs = []
    count = 0
    for pi in pinvs:
        if count % 10 == 0:
            print('#', end='')
            sys.stdout.flush()
        count += 1
        # need to be able to look up from negated primed invariants
        npinv = Not(pi._expr)
        orig_inv = pinv2inv[pi]
        # check if it's inductive by itself
        if check_single_inv_induction(ind_solver, orig_inv._expr, npinv):
            continue
        mucs.append((orig_inv, get_deps(constraints, npinv)))

#    debug_printing(pinv2inv, mucs, clause_trans)

    print('\nBuilding graph...')
    dot = Digraph(comment="Induction Graph")

    if len(invs) < 100:
        for inv in invs:
            dot.node(str(inv._id))
        for (inv, deps) in mucs:
            for d in deps:
                if d != inv and d != clause_trans:
                    dot.edge(str(inv._id), str(d._id), label=None)
    else:
        # for very large invariants, generate nodes lazily
        nodes = set()
        for (inv, deps) in mucs:
            if len(deps) == 0:
                continue
            if inv._id not in nodes:
                nodes.add(inv._id)
                dot.node(str(inv._id))
            for d in deps:
                if d != inv and d != clause_trans:
                    if d._id not in nodes:
                        nodes.add(d._id)
                        dot.node(str(d._id))
                    dot.edge(str(inv._id), str(d._id), label=None)

    dot.render('./%s.dot'%outname)

    print('==================== completed ====================')


if __name__ == "__main__":
    main()
