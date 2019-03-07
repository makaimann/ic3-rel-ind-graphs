#!/usr/bin/env python3
# obtained from: https://www.geeksforgeeks.org/strongly-connected-components/

# Python implementation of Kosaraju's algorithm to print all SCCs

from collections import defaultdict

#This class represents a directed graph using adjacency list representation
class Graph:

    def __init__(self,vertices):
        self.V= vertices #No. of vertices
        self.graph = defaultdict(list) # default dictionary to store graph

    # function to add an edge to graph
    def addEdge(self,u,v):
        self.graph[u].append(v)

    # A function used by DFS
    def DFSUtil(self,v,visited, rev):
        # Mark the current node as visited and print it
        visited[v]= True
        print(rev[v], end=" ")
        #Recur for all the vertices adjacent to this vertex
        for i in self.graph[v]:
            if visited[i]==False:
                self.DFSUtil(i,visited, rev)


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
    def printSCCs(self, rev):

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
        while stack:
            i = stack.pop()
            if visited[i]==False:
                gr.DFSUtil(i, visited, rev)
                print()

if __name__ == "__main__":
    import argparse
    import pickle
    import sys

    parser = argparse.ArgumentParser(description="Find Strongly Connected Components")
    parser.add_argument('input_file', help='Pickled list of edges')
    args = parser.parse_args()

    edges = pickle.load(open(args.input_file, 'rb'))

    d = dict()
    count = 0
    for n1, n2 in edges:
        if n1 not in d:
            d[n1] = count
            count += 1
        if n2 not in d:
            d[n2] = count
            count += 1

    # Create a graph given in the above diagram
    g = Graph(count)

    for n1, n2 in edges:
        g.addEdge(d[n1], d[n2])

    print ("Following are strongly connected components " +
           "in given graph")

    rev = {v:k for k, v in d.items()}
    g.printSCCs(rev)
    #This code is contributed by Neelam Yadav
