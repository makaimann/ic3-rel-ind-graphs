#!/usr/bin/env python3
# obtained from: https://www.geeksforgeeks.org/strongly-connected-components/

# Python implementation of Kosaraju's algorithm to get SCCs
# The original code was contributed by Neelam Yadav
#     original code has been modified here

import argparse
from collections import defaultdict
import pathlib
import pickle
import sys

#This class represents a directed graph using adjacency list representation
class Graph:

    def __init__(self,vertices):
        self.V= vertices #No. of vertices
        self.graph = defaultdict(list) # default dictionary to store graph

    # function to add an edge to graph
    def addEdge(self,u,v):
        self.graph[u].append(v)

    # A function used by DFS
    def DFSUtil(self,v,visited):
        # Mark the current node as visited and print it
        visited[v]= True
        yield v
        #Recur for all the vertices adjacent to this vertex
        for i in self.graph[v]:
            if visited[i]==False:
                yield from self.DFSUtil(i,visited)


    def fillOrder(self,v,visited, stack):
        # Mark the current node as visited
        visited[v]= True
        #Recur for all the vertices adjacent to this vertex
        for i in self.graph[v]:
            if visited[i]==False:
                self.fillOrder(i, visited, stack)
        stack = stack.append(v)


    # Function that returns reverse (or transpose) of this graph
    def getTranspose(self):
        g = Graph(self.V)

        # Recur for all the vertices adjacent to this vertex
        for i in self.graph:
            for j in self.graph[i]:
                g.addEdge(j,i)
        return g



    # The main function that finds and prints all strongly
    # connected components
    def getSCCs(self):

        stack = []
        # Mark all the vertices as not visited (For first DFS)
        visited =[False]*(self.V)
        # Fill vertices in stack according to their finishing
        # times
        for i in range(self.V):
            if visited[i]==False:
                self.fillOrder(i, visited, stack)

        # Create a reversed graph
        gr = self.getTranspose()

        # Mark all the vertices as not visited (For second DFS)
        visited =[False]*(self.V)

        # Now process all vertices in order defined by Stack
        sccs = []
        while stack:
            i = stack.pop()
            if visited[i]==False:
                sccs.append(list(gr.DFSUtil(i, visited)))
        return sccs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find Strongly Connected Components")
    parser.add_argument('input_file', help='Pickled list of edges (.pkl), or string of hyperedges that can be evaluated (.out)')
    parser.add_argument('--proc', metavar="<PROC_TYPE>", choices=['list', 'num', 'hist'],
                        help='The type of processing to do: <list|num|hist>', default='list')
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
            nodes.add(n1)
            nodes.add(n2)
    elif input_file.suffix == '.out':
        hyperedges = eval(input_file.open().read())
        # expand the hyperedges
        edges = []
        for src_node, dst_nodes in hyperedges:
            nodes.add(src_node)
            if len(dst_nodes) > 0:
                # FIXME - just picking the first MUC
                for dn in dst_nodes[0]:
                    edges.append((src_node, dn))
                    nodes.add(dn)

    if proc not in {'list', 'num', 'hist'}:
        raise NotImplementedError("{} processing not implemented".format(proc))

    if remove:
        print('removing', remove)
        edges = list(filter(lambda nodes: nodes[0] not in remove and nodes[1] not in remove, edges))

    d = dict()
    count = 0
    for node in nodes:
        if node not in d:
            d[node] = count
            count += 1

    # Create a graph given in the above diagram
    g = Graph(count)

    for n1, n2 in edges:
        g.addEdge(d[n1], d[n2])

    rev = {v:k for k, v in d.items()}
    sccs = g.getSCCs()

    if proc == "list":
        print ("Following are strongly connected components " +
               "in given graph")
        for scc in sccs:
            for n in scc:
                print(rev[n], end=' ')
            print()
    elif proc == "num":
        print('Found {} SCCs of the following lengths:'.format(len(sccs)))
        hist = defaultdict(int)
        for scc in sccs:
            hist[len(scc)] += 1
        print(hist)
    elif proc == "hist":
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
