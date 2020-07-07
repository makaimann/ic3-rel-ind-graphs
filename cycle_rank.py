#!/usr/bin/env python3
import argparse
from copy import deepcopy
from pathlib import Path
import pickle
from graph import Graph
from graph_utils import is_acyclic, get_scc_graphs, print_graph


def compute_cycle_rank_rec(g:Graph)->int:
    if is_acyclic(g):
        return 0
    else:
        sccs = get_scc_graphs(g)
        assert len(sccs) > 0

        scc_cycle_ranks = []
        for scc in sccs:
            rm_node_cycle_ranks = []
            for n in self.nodes:
                scc_m_n = deepcopy(g)
                scc_m_n.rmNode(n)
                rm_node_cycle_ranks.append(compute_cycle_rank_res(scc_m_n))
            scc_cycle_ranks.append(1 + min(rm_node_cycle_ranks))
        return max(scc_cycle_ranks)



def compute_cycle_rank(g:Graph)->int:
    if is_acyclic(g):
        return 0
    else:
        sccs = get_scc_graphs(g)
        assert len(sccs) > 0

        if len(sccs) == 1:
            return compute_cycle_rank_rec(g)
        else:
            cycle_ranks = []
            for scc in sccs:
                cycle_ranks.append(compute_cycle_rank_rec(scc))
            return max(cycle_ranks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Read in pickle graph and compute cycle rank")
    parser.add_argument('input_file', help='Pickled list of edges (.pkl)')
    parser.add_argument('-p', '--print-graph', action='store_true', help='Print the graph')

    args = parser.parse_args()
    input_file = Path(args.input_file)

    nodes = set()
    edges = pickle.load(input_file.open('rb'))
    for n1, n2 in edges:
        n1 = str(n1)
        n2 = str(n2)
        nodes.add(n1)
        nodes.add(n2)
    g = Graph(list(nodes))
    for n1, n2 in edges:
        g.addEdge(n1, n2)

    if args.print_graph:
        print("Computing Cycle Rank of graph:")
        print_graph(g)
        print()
