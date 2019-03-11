from typing import Dict, List, Sequence

from z3 import And, Bool, BoolRef, ExprRef, Not, Or, Solver, unsat, sat

varmap = {}

class Clause(object):
    clause_cache = dict()
    def __new__(cls, expr:ExprRef):
        if expr.get_id() in Clause.clause_cache:
            return Clause.clause_cache[expr.get_id()]
        else:
            return super(Clause, cls).__new__(cls)

    def __init__(self, expr:ExprRef):
        self._id = expr.get_id()
        self._expr = expr
        Clause.clause_cache[self._id] = self

    def __hash__(self):
        return hash(self._expr)

    def __eq__(self, other):
        if not isinstance(other, Clause):
            return NotImplementedError
        else:
            return self._id == other._id

    def __ne__(self, other):
        if not isinstance(other, Clause):
            return NotImplementedError
        else:
            return self._id != other._id

    def __str__(self):
        return self._expr.sexpr()

    def __repr__(self):
        return self._expr.sexpr()


def get_lit(litstr:str) -> BoolRef:
    sign = litstr[0] == '-'
    if sign:
        litstr = litstr[1:]
    try:
        l = varmap[litstr]
        if sign:
            l = Not(l)
        return l
    except:
        v = Bool('l' + litstr)
        varmap[litstr] = v
        if sign:
            l = Not(v)
        else:
            l = v
        return l


def read_cnf(filename:str) -> List[Clause]:
    clauses = []
    f = open(filename, 'r')
    for line in f.read().split('\n'):
        line = line.strip()
        # ignore the zero termination
        if line[-2:] == " 0":
            line = line[:-2]
        if not line:
            continue
        if line[0] == 'p' or line[0] == 'c':
            continue
        clauses.append(Clause(Or(list(map(get_lit, line.split())))))
    f.close()
    return clauses


def assert_clauses(slv:Solver, clauses:Sequence[Clause]):
    slv.add(And([c._expr for c in clauses]))


def check_inductiveness(slv:Solver, inv2pinv:Dict[Clause, Clause])->bool:
    # assumes trans has already been added to solver
    slv.push()
    assert_clauses(slv, inv2pinv.keys())
    slv.add(Not(And([c._expr for c in inv2pinv.values()])))
    # it's inductive if check is unsat
    res = str(slv.check()) == "unsat"
    slv.pop()
    return res

def identify_invariants(trans:List[Clause], inv_cand:List[Clause], inv_primed_cand:List[Clause]):
    inv2pinv = dict(zip(inv_cand, inv_primed_cand))
    slv = Solver()
    assert_clauses(slv, trans)
    print("Checking {} candidate invariants...".format(len(inv_cand)))

    while not check_inductiveness(slv, inv2pinv):
        print('checking')
        slv.push()
        assert_clauses(slv, inv2pinv.keys())
        for ic in [i for i in inv2pinv.keys()]:
            slv.push()
            ipc = inv2pinv[ic]
            slv.add(Not(ipc._expr))
            if slv.check() == sat:
                del inv2pinv[ic]
            slv.pop()
        slv.pop()
    print("Found {} invariants".format(len(inv2pinv)))
    return inv2pinv
