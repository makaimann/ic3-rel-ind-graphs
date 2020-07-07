from collections import defaultdict

from typing import Any, Dict, List, Optional, Set

class Graph:

    def __init__(self, nodes:List[str])->None:
        self.nodes = list(nodes)
        self.edges = defaultdict(list)

    def addEdge(self, u:str, v:str):
        self.edges[u].append(v)

    def rmNode(self, u:str):
        del self.edges[u]
        self.nodes.remove(u)
        for sinks in self.edges.values():
            try:
                sinks.remove(u)
            except:
                pass

    @property
    def leaves(self):
        for n in self.nodes:
            if not self.edges[n]:
                yield n

    def transpose(self):
        gt = Graph(self.nodes)

        # reverse all the edges
        for s, dns in self.edges.items():
            for dn in dns:
                gt.addEdge(dn, s)
        return gt
