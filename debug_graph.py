#!/usr/bin/env python3
"""
Debug script to understand the graph structure and traversal
"""

import sys
import os
sys.path.insert(0, './python-utils/')

from graph import Graph
import logging

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    return logging.getLogger(__name__)

def debug_graph():
    logger = setup_logging()
    graph = Graph(logger)
    
    # Add the same edges as in the example
    graph.addEdge("pthread_create", "syscall( 56 )")
    graph.addEdge("fopen", "_IO_file_open")
    graph.addEdge("_IO_file_open", "syscall( 2 )")
    graph.addEdge("_IO_file_open", "syscall( 3 )")
    
    print("Graph structure:")
    print(f"All nodes: {graph.getAllNodes()}")
    print(f"Adjacency graph: {graph.adjGraph}")
    print()
    
    # Test getLeavesFromStartNode
    print("Testing getLeavesFromStartNode:")
    
    # Test with pthread_create
    print("\nFor pthread_create:")
    leaves = graph.getLeavesFromStartNode("pthread_create", ["syscall( 56 )"], [])
    print(f"Leaves found: {leaves}")
    
    # Test with fopen
    print("\nFor fopen:")
    leaves = graph.getLeavesFromStartNode("fopen", ["syscall( 2 )", "syscall( 3 )"], [])
    print(f"Leaves found: {leaves}")
    
    # Check if syscall nodes are actually leaf nodes
    print("\nChecking if syscall nodes are leaf nodes:")
    for node in ["syscall( 56 )", "syscall( 2 )", "syscall( 3 )"]:
        neighbors = graph.adjGraph.get(node, [])
        print(f"{node}: neighbors = {neighbors}, is_leaf = {len(neighbors) == 0}")

if __name__ == "__main__":
    debug_graph()