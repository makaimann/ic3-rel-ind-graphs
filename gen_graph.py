#!/usr/bin/env python3
import argparse
from cnf_utils import read_cnf, assert_clauses, check_inductiveness, identify_invariants, Clause
from collections import deque
from graphviz import Digraph
from itertools import chain
from marco import SubsetSolver, MapSolver, enumerate_sets
import pickle
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
            # FIXME: do constraints never show up in the core? Seems like we could get a key error
            current = set(indicator2idx[ind.get_id()] for ind in core)
        else:
            current.add(i)
    assert not check_subset(current), "Expecting unsat at end of get_mus"
    return [constraints[i] for i in current]

def get_deps(constraints, npinv):
    constraints = constraints[:]
    constraints.append(npinv)

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
    res = solver.check() == unsat
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
    parser.add_argument('-o', dest='outname', default='out',
                        metavar='<OUTPUT_FILE>',
                        help='Filename to write the graphviz graph to.')
    parser.add_argument('--pickle', dest='gen_pickle', action="store_true",
                        help='Generate a pickle file of the edges.')
    parser.add_argument('--noprop', dest='noprop', action="store_true",
                        help='Don\'t include prop in invariants')
    args = parser.parse_args()
    trans = read_cnf(args.trans_filename)
    inv_cand = read_cnf(args.invcand_filename)
    inv_primed_cand = read_cnf(args.invprime_cand_filename)
    outname = args.outname
    gen_pickle = args.gen_pickle
    noprop = args.noprop

    # label each clause in the invariant with its position
    # zero is the property
    labels = dict()
    for i, clause in enumerate(inv_cand):
        labels[clause._id] = i

    # the first invariant is assumed to be the property
    # we don't want to remove that, so take it out now and add it back afterwards
    prop = inv_cand[0]
    primeprop = inv_primed_cand[0]

    if noprop:
        inv_cand = inv_cand[1:]
        inv_primed_cand = inv_primed_cand[1:]

    inv2pinv = dict(zip(inv_cand, inv_primed_cand))

    z3trans = And([c._expr for c in trans])
    clause_trans = Clause(z3trans)

    if not noprop:
        assert prop in inv2pinv

    invs = inv2pinv.keys()
    pinvs = inv2pinv.values()

    print("Finding dependencies...")

    constraints = [z3trans]
    for inv in invs:
        constraints.append(inv._expr)

    ind_solver = Solver()
    ind_solver.add(z3trans)

#    debug_printing(inv2pinv, clause_trans, prop, include_mapping=True)
    edges = []
    if noprop:
        for inv in invs:
            pinv = inv2pinv[inv]
            npinv = Not(pinv._expr)
            invdeps = get_deps(constraints, npinv)
            if clause_trans in invdeps:
                invdeps.remove(clause_trans)
            for d in invdeps:
                edges.append((str(inv._id), str(d._id)))
    else:
        to_visit = deque([prop])
        visited = set()
        count = 0
        while to_visit:
            if count % 20 == 0:
                print('#', end='')
                sys.stdout.flush()

            inv = to_visit.pop()
            pinv = inv2pinv[inv]

            if inv == prop:
                assert labels[inv._id] == 0
                strinv = '0 (Prop)'
            else:
                strinv = str(labels[inv._id])

    #        print('visiting', inv._id, pinv._id)

            if inv in visited:
    #            print('skipping because already in visited')
                continue
            else:
                visited.add(inv)
                npinv = Not(pinv._expr)
                invdeps = get_deps(constraints, npinv)
    #            print("invdeps", [i._id for i in invdeps])
                try:
                    invdeps.remove(clause_trans)  # trans is implicit
                except:
                    pass
                try:
                    invdeps.remove(inv) # don't have self loops
                except:
                    pass
                for d in invdeps:
                    if d == prop:
                        assert labels[d._id] == 0
                        strd = '0 Prop'
                    else:
                        strd = str(labels[d._id])
                    edges.append((strinv, strd))
                    if d not in visited:
                        to_visit.appendleft(d)
            count += 1

    print()
    # pickle the graph
    if gen_pickle:
        print('Pickling to %s.pkl'%outname)
        f = open('%s.pkl'%outname, 'wb')
        pickle.dump(edges, f)
        f.close()
    # end pickling the graph

    print('Writing graph to {}.dot'.format(outname))
    f = open('%s.dot'%outname, 'w')
    f.write('// Induction Graph of %s\ndigraph{\n'%outname)
    for n1, n2 in edges:
        f.write("  {} -> {}\n".format(n1, n2))
    f.write("}")
    f.close()


    # dot = Digraph(comment="Induction Graph")
    # dot.edges(edges)
    # dot.render('./%s.dot'%outname)

    print('\n==================== completed ====================')
    # print sat so it's not counted as an error on the cluster
    print("sat")


if __name__ == "__main__":
    main()
