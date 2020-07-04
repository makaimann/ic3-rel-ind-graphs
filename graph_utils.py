from graph import Graph

from copy import deepcopy



def is_acyclic(g_in:Graph):
    g = deepcopy(g_in)
    return is_acyclic_recurse(g)

def is_acyclic_recurse(g:Graph):
    if not g.nodes:
        return True
    else:
        leaves = set(g.leaves)

        if not leaves:
            return False

        for n in leaves:
            g.rmNode(n)
        return is_acyclic(g)
