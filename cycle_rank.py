#!/usr/bin/env python3
import argparse
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import pickle
from graph import Graph
from graph_utils import is_acyclic, get_scc_graphs, print_graph


def compute_cycle_rank(g:Graph)->int:
    if not g.nodes:
        return 0
    # TODO: what about empty edges?
    #       not explicitly handled in https://en.wikipedia.org/wiki/Cycle_rank
    elif is_acyclic(g):
        return 0
    else:
        sccs = get_scc_graphs(g)
        assert len(sccs) > 0

        scc_cycle_ranks = []
        for scc in sccs:
            rm_node_cycle_ranks = []
            if len(scc.nodes) == 1:
                scc_cycle_ranks.append(0)
            else:
                for n in scc.nodes:
                    scc_m_n = deepcopy(scc)
                    scc_m_n.rmNode(n)
                    rm_node_cycle_ranks.append(compute_cycle_rank(scc_m_n))
                scc_cycle_ranks.append(1 + min(rm_node_cycle_ranks))
        return max(scc_cycle_ranks)

def compute_cycle_rank_iter(g:Graph)->int:
    if is_acyclic(g):
        return 0

    def graph2id(graph:Graph)->str:
        # graph keeps them sorted
        return "_".join(graph.nodes)

    process_stack = [g]
    visited = set()
    processed = set()
    graph_cycle_rank = {}
    # maps from sorted node string to the children of that graph
    scc_children = defaultdict(list)
    rm_node_children = defaultdict(list)
    while process_stack:
        graph = process_stack.pop()
        id_ = graph2id(graph)
        if id_ in graph_cycle_rank:
            # cache hit
            pass
        elif id_ not in visited:
            visited.add(id_)
            process_stack.append(graph)

            if not graph.nodes:
                graph_cycle_rank[id_] = 0
            elif is_acyclic(graph):
                graph_cycle_rank[id_] = 0
            elif len(graph.nodes) == 1:
                # cyclic graph with single node: n -> n
                # TODO should this be 1 or 0: 1 feels right to me
                graph_cycle_rank[id_] = 1
            else:
                sccs = get_scc_graphs(graph)
                for scc in sccs:
                    if len(sccs) > 1:
                        # if there's only one scc, then it's not a child
                        scc_children[id_].append(scc)
                    scc_id = graph2id(scc)
                    process_stack.append(scc)
                    if is_acyclic(scc):
                        graph_cycle_rank[scc_id] = 0
                    else:
                        for n in scc.nodes:
                            scc_copy = deepcopy(scc)
                            scc_copy.rmNode(n)
                            scc_copy_id = graph2id(scc_copy)
                            if not scc_copy.nodes:
                                # can happen if graph was n -> n
                                graph_cycle_rank[scc_copy_id] = 0
                                continue
                            assert scc_copy.nodes
                            process_stack.append(scc_copy)
                            rm_node_children[scc_id].append(scc_copy)
        elif id_ in scc_children:
            assert id_ not in processed
            graph_cycle_rank[id_] = max([graph_cycle_rank[graph2id(gg)] for gg in scc_children[id_]])
            del scc_children[id_]
            processed.add(id_)
        else:
            assert id_ not in processed
            assert id_ in rm_node_children
            graph_cycle_rank[id_] = 1 + min([graph_cycle_rank[graph2id(gg)] for gg in rm_node_children[id_]])
            del rm_node_children[id_]
            processed.add(id_)

    return graph_cycle_rank[id_]



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

    cycle_rank = compute_cycle_rank_iter(g)
    assert cycle_rank >= 0, "Expecting a non-negative cycle rank"
    print("Cycle rank is", cycle_rank)
