from graph import Graph

from graph_utils import is_acyclic


def test_is_acyclic_tree():
    g = Graph(['1', '2', '3', '4', '5'])
    g.addEdge('1', '2')
    g.addEdge('2', '3')
    g.addEdge('2', '4')
    g.addEdge('4', '5')

    assert is_acyclic(g)
