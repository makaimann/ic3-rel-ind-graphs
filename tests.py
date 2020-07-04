from graph import Graph

from graph_utils import is_acyclic


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
