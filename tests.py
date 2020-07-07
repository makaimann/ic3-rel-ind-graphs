from graph import Graph

from graph_utils import is_acyclic, print_graph, get_scc_graphs, bfs, dfs


def test_is_acyclic_tree():
    g = Graph(['1', '2', '3', '4', '5'])
    g.addEdge('1', '2')
    g.addEdge('2', '3')
    g.addEdge('2', '4')
    g.addEdge('4', '5')

    assert is_acyclic(g)


def test_is_acyclic_dag():
    g = Graph(['1', '2', '3', '4', '5', '6'])
    g.addEdge('1', '2')
    g.addEdge('2', '3')
    g.addEdge('2', '4')
    g.addEdge('4', '5')
    g.addEdge('5', '6')
    g.addEdge('2', '6')

    assert is_acyclic(g)

def test_is_acyclic_cyclic():
    g = Graph(['1', '2', '3', '4', '5', '6'])
    g.addEdge('1', '2')
    g.addEdge('2', '3')
    g.addEdge('2', '4')
    g.addEdge('4', '5')
    g.addEdge('5', '6')
    g.addEdge('2', '6')
    g.addEdge('6', '4')

    assert not is_acyclic(g)

def test_rm_node():
    g = Graph(['1', '2', '3', '4', '5', '6'])
    g.addEdge('1', '2')
    g.addEdge('2', '3')
    g.addEdge('2', '4')
    g.addEdge('4', '5')
    g.addEdge('5', '6')
    g.addEdge('2', '6')
    g.addEdge('6', '4')

    assert not is_acyclic(g)

    g.rmNode('6')

    assert is_acyclic(g)

def test_sccs():
    # graph copied from: https://www.geeksforgeeks.org/strongly-connected-components/
    g = Graph(['0', '1', '2', '3', '4'])
    g.addEdge('0', '3')
    g.addEdge('0', '2')
    g.addEdge('2', '1')
    g.addEdge('1', '0')
    g.addEdge('3', '4')

    print('Finding SCCs for graph')
    print_graph(g)

    sccs = get_scc_graphs(g)

    assert len(sccs) == 3, 'should have 3 sccs'

    print('SCCS:')
    visited_nodes = set()
    for i, scc in enumerate(sccs):
        print("SCC", i)
        scc_nodes = set(scc.nodes)
        visited_nodes_dfs = set(dfs(scc))
        assert visited_nodes_dfs == scc_nodes, "by definition should reach all nodes"

        print_graph(scc)

        # shouldn't matter if it's dfs or bfs
        visited_nodes_bfs_dict = bfs(scc, scc.nodes[0])
        assert set(visited_nodes_bfs_dict.keys()) == scc_nodes, "by definition should reach all nodes"

        # should only include edges in the SCC
        edge_nodes = set()
        for n, sinks in scc.edges.items():
            edge_nodes.add(n)
            for s in sinks:
                edge_nodes.add(s)
        assert edge_nodes == visited_nodes_dfs

        for n in edge_nodes:
            assert n not in visited_nodes, 'should only appear in one SCC'
            visited_nodes.add(n)

