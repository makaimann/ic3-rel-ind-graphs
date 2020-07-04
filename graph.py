class Graph:

    def __init__(self, nodes:List[str])->None:
        self.nodes = nodes
        self.edges = defaultdict(list)

    def addEdge(self, u:str, v:str):
        self.edges[u].append(v)

    def rmNode(self, u:str):
        del self.edges[u]
        for sinks in self.edges.values():
            sinks.remove(u)

    def transpose(self):
        gt = Graph(self.nodes)

        # reverse all the edges
        for s, dns in self.edges.items():
            for dn in dns:
                gt.addEdge(dn, s)
        return gt
