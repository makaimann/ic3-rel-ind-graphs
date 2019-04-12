#!/usr/bin/env python3
# obtained from: https://www.geeksforgeeks.org/strongly-connected-components/

# Python implementation of Kosaraju's algorithm to get SCCs
# The original code was contributed by Neelam Yadav
#     original code has been modified here

import argparse
from collections import defaultdict, deque
import pathlib
import pickle
import sys
from typing import List, Optional, Set, Dict

PROP='Prop'

class Graph:

    def __init__(self, nodes:List[int])->None:
        self.nodes = nodes
        self.edges = defaultdict(list)

    def addEdge(self, u, v):
        self.edges[u].append(v)

    def transpose(self):
        gt = Graph(self.nodes)

        # reverse all the edges
        for s, dns in self.edges.items():
            for dn in dns:
                gt.addEdge(dn, s)
        return gt

def dfs(g:Graph)->List[int]:
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

    assert len(finish_stack) == len(g.nodes)
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

def get_sccs(g:Graph)->List[Set[int]]:
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

# Simple Test
# if __name__ == "__main__":
#     g = Graph([0, 1, 2, 3, 4])
#     g.addEdge(1, 0)
#     g.addEdge(0, 2)
#     g.addEdge(2, 1)
#     g.addEdge(0, 3)
#     g.addEdge(3, 4)

#     sccs = get_sccs(g)
#     print(sccs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find Strongly Connected Components")
    parser.add_argument('input_file', help='Pickled list of edges (.pkl), or string of hyperedges that can be evaluated (.out)')
    parser.add_argument('--proc', metavar="<PROC_TYPE>", choices=['list', 'num', 'hist', 'bfs'],
                        help='The type of processing to do: <list|num|hist>', default='num')
    parser.add_argument('--remove', metavar="<NODES_TO_REMOVE>", help='A semicolon delimited list of node names to remove', default='')
    args = parser.parse_args()

    proc = args.proc
    remove = args.remove
    input_file = pathlib.Path(args.input_file)

    remove = remove.split(';')
    if '' in remove:
        remove.remove('')

    # include nodes so that we still get a result even if there are no edges
    # Note: this won't happen with the pickled edge files because there would be no edges listed
    nodes = set()
    if input_file.suffix == '.pkl':
        edges = pickle.load(input_file.open('rb'))
        for n1, n2 in edges:
            n1 = str(n1)
            n2 = str(n2)
            nodes.add(n1)
            nodes.add(n2)
    elif input_file.suffix == '.out':
        hyperedges = eval(input_file.open().read())
        # expand the hyperedges
        edges = []
        for src_node, dst_nodes in hyperedges:
            src_node = str(src_node)
            nodes.add(src_node)
            if len(dst_nodes) > 0:
                # FIXME - just picking the first MUC
                for dn in (str(d) for d in dst_nodes[0]):
                    edges.append((src_node, dn))
                    nodes.add(dn)

    if remove:
        print('Removing', remove)
        for r in remove:
            assert r in nodes, "Expecting node to be removed, '{}' to be in the set of nodes".format(r)
            nodes.remove(r)
        edge_len = len(edges)
        edges = list(filter(lambda nodes: nodes[0] not in remove and nodes[1] not in remove, edges))
        print("Removed {} edges".format(edge_len - len(edges)))

    to_graph_node = dict()
    dist = 0
    for node in nodes:
        if node not in to_graph_node:
            to_graph_node[node] = dist
            dist += 1

    # Create a graph given in the above diagram
    g = Graph(list(to_graph_node.values()))

    for n1, n2 in edges:
        g.addEdge(to_graph_node[n1], to_graph_node[n2])

    from_graph_node = {v:k for k, v in to_graph_node.items()}

    if proc == "list":
        sccs = get_sccs(g)
        print ("Following are strongly connected components " +
               "in given graph")
        for scc in sccs:
            for n in scc:
                print(from_graph_node[n], end=' ')
            print()
    elif proc == "num":
        sccs = get_sccs(g)
        print('Found {} SCCs of the following lengths:'.format(len(sccs)))
        hist = defaultdict(int)
        for scc in sccs:
            hist[len(scc)] += 1
        print(hist)
    elif proc == "hist":
        sccs = get_sccs(g)
        from matplotlib import pyplot as plt

        hist = defaultdict(int)
        for scc in sccs:
            hist[len(scc)] += 1

        length, freq = zip(*sorted(hist.items()))
        length = list(map(int, length))
        freq = list(map(int, freq))
        x_pos = list(range(len(length)))
        plt.bar(x_pos, freq, align='center')
        plt.xticks(x_pos, length)
        plt.xlabel('Size of SCC')
        plt.ylabel('Number of SCCs')
        plt.title('Occurrences of SCC sizes')
        plt.show()
    elif proc == 'bfs':
        labeled_nodes = bfs(g, to_graph_node[PROP])
        max_distance = max(filter(lambda x: x is not None, labeled_nodes.values()))
        bfs_count = [0]*(max_distance+1)

        for n, dist in labeled_nodes.items():
            if dist is None:
                continue
            else:
                bfs_count[dist] += 1

        print(bfs_count)
