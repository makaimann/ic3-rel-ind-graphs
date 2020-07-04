from graph import Graph

from collections import defaultdict
from copy import deepcopy

from typing import Any, Dict, List, Optional, Set


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


def dfs(g:Graph)->List[str]:
    '''
    Returns a "finish stack" where nodes have been added to the stack when
    every path from that node has already been explored
    '''

    # which have been added to the finish_stack
    # cheaper to query a set for membership, so duplicating storage
    processed = set()
    finish_stack = []

    visited = defaultdict(bool)
    for start in g.nodes:
        if visited[start]:
            continue
        dfs_stack = [start]
        while dfs_stack:
            n = dfs_stack.pop()
            if not visited[n]:
                dfs_stack.append(n)
                visited[n] = True
                for dn in g.edges[n]:
                    if not visited[dn]:
                        assert dn not in processed
                        dfs_stack.append(dn)
            else:
                if n not in processed:
                    assert sum(1 for x in g.edges[n] if not visited[x]) == 0, \
                        "Expecting all DFS paths from this node to have already been explored"
                    processed.add(n)
                    # make sure it's not in the dfs_stack
                    if n not in finish_stack:
                        # finished DFS at this node
                        finish_stack.append(n)

    assert len(finish_stack) == len(g.nodes), \
        "Expected all nodes to be covered but only got {}/{}".format(len(finish_stack), len(g.nodes))
    return finish_stack

def bfs(g:Graph, start:int)->Dict[int, Optional[int]]:
    '''
    Takes a graph and starting node and returns a dictionary labeling the distance from the start node
    for each node in the graph.
    '''
    assert start in g.nodes, "Expecting start node to be in nodes"

    labeled_nodes = dict()
    for n in g.nodes:
        labeled_nodes[n] = None

    visited = defaultdict(bool)
    queue = deque([start])
    labeled_nodes[start] = 0
    while queue:
        n = queue.popleft()
        if not visited[n]:
            visited[n] = True
            for dn in g.edges[n]:
                queue.append(dn)
                if labeled_nodes[dn] is None: # first time we've encountered this node so far
                    assert labeled_nodes[n] is not None, "Expecting previous node to have a distance"
                    labeled_nodes[dn] = labeled_nodes[n] + 1

    return labeled_nodes

def get_sccs(g:Graph)->List[Set[str]]:
    sccs = []

    finish_stack = dfs(g)
    gt = g.transpose()

    # reverse dfs to get SCCs
    visited = defaultdict(bool)
    while finish_stack:
        start = finish_stack.pop()
        if visited[start]:
            continue
        scc = set()
        dfs_stack = [start]
        while dfs_stack:
            n = dfs_stack.pop()
            if not visited[n]:
                dfs_stack.append(n)
                scc.add(n)
                visited[n] = True
                for dn in gt.edges[n]:
                    if not visited[dn]:
                        dfs_stack.append(dn)
        sccs.append(scc)
    return sccs
