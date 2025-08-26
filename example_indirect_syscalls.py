#!/usr/bin/env python3
"""
Example demonstrating how indirect syscalls via libc are discovered.
This script shows the complete workflow from binary analysis to syscall discovery.
"""

import sys
import os
sys.path.insert(0, './python-utils/')

from graph import Graph
import logging

def setup_logging():
    """Setup basic logging for the example"""
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    return logging.getLogger(__name__)

def create_sample_call_graph():
    """Create a small sample call graph to demonstrate the concept"""
    logger = setup_logging()
    graph = Graph(logger)
    
    # Add sample call relationships that mimic real libc behavior
    # These represent function calls that eventually lead to syscalls
    
    # pthread_create directly calls syscall(56) - clone
    graph.addEdge("pthread_create", "syscall( 56 )")
    
    # fopen calls _IO_file_open which calls multiple syscalls
    graph.addEdge("fopen", "_IO_file_open")
    graph.addEdge("_IO_file_open", "syscall( 2 )")   # open
    graph.addEdge("_IO_file_open", "syscall( 3 )")   # close
    graph.addEdge("_IO_file_open", "syscall( 322 )") # fstatat64
    
    # read calls _IO_file_read which calls read syscall
    graph.addEdge("read", "_IO_file_read")
    graph.addEdge("_IO_file_read", "syscall( 0 )")   # read
    
    # write calls _IO_file_write which calls write syscall
    graph.addEdge("write", "_IO_file_write")
    graph.addEdge("_IO_file_write", "syscall( 1 )")  # write
    
    # malloc calls _int_malloc which calls mmap syscall
    graph.addEdge("malloc", "_int_malloc")
    graph.addEdge("_int_malloc", "syscall( 9 )")     # mmap
    
    return graph

def demonstrate_indirect_syscall_discovery():
    """Demonstrate the complete indirect syscall discovery process"""
    logger = setup_logging()
    
    print("=== INDIRECT SYSCALL DISCOVERY DEMONSTRATION ===\n")
    
    # Step 1: Create the call graph
    print("Step 1: Loading libc call graph...")
    call_graph = create_sample_call_graph()
    print(f"   - Call graph loaded with {call_graph.getNodeCount()} nodes")
    print()
    
    # Step 2: Simulate imported functions from a binary
    print("Step 2: Analyzing imported functions from binary...")
    imported_functions = ["pthread_create", "fopen", "read", "write", "malloc"]
    print(f"   - Imported functions: {imported_functions}")
    print()
    
    # Step 3: Generate syscall patterns to look for
    print("Step 3: Generating syscall patterns to search for...")
    syscall_patterns = []
    for i in range(400):  # Include all syscalls up to 400 as in the real system
        syscall_patterns.append(f"syscall( {i} )")
        syscall_patterns.append(f"syscall( {i} )")  # Add both formats
    print(f"   - Looking for patterns like: {syscall_patterns[:5]}...")
    print()
    
    # Step 4: Discover indirect syscalls for each imported function
    print("Step 4: Discovering indirect syscalls...")
    all_discovered_syscalls = set()
    
    for func in imported_functions:
        print(f"   Analyzing function: {func}")
        
        # Use the same method as the real system
        leaves = call_graph.getLeavesFromStartNode(func, syscall_patterns, [])
        
        if leaves:
            syscalls = []
            for leaf in leaves:
                # Extract syscall number from pattern like "syscall( 56 )"
                if leaf.startswith("syscall(") and leaf.endswith(")"):
                    syscall_num = leaf[8:-1].strip()
                    try:
                        syscalls.append(int(syscall_num))
                    except ValueError:
                        pass
            
            if syscalls:
                print(f"     -> Discovered syscalls: {syscalls}")
                all_discovered_syscalls.update(syscalls)
            else:
                print(f"     -> No syscalls found")
        else:
            print(f"     -> No leaf nodes found")
    
    print()
    
    # Step 5: Show final results
    print("Step 5: Final Results")
    print(f"   - Total unique syscalls discovered: {len(all_discovered_syscalls)}")
    print(f"   - Syscall numbers: {sorted(all_discovered_syscalls)}")
    
    # Map syscall numbers to names for clarity
    syscall_names = {
        0: "read",
        1: "write", 
        2: "open",
        3: "close",
        9: "mmap",
        56: "clone",
        322: "fstatat64"
    }
    
    print("\n   - Syscall mapping:")
    for num in sorted(all_discovered_syscalls):
        name = syscall_names.get(num, f"unknown_{num}")
        print(f"     {num:3d} -> {name}")
    
    print("\n=== DEMONSTRATION COMPLETE ===")

def show_real_call_graph_example():
    """Show a real example from the actual call graph files"""
    print("\n=== REAL CALL GRAPH EXAMPLE ===\n")
    
    # Show some real entries from the glibc call graph
    print("Real entries from glibc.callgraph:")
    print("pthread_create : syscall( 56 )")
    print("_IO_file_open : syscall( 2 )")
    print("_IO_file_open : syscall( 3 )")
    print("_IO_file_open : syscall( 322 )")
    print()
    
    print("This means:")
    print("- pthread_create directly calls syscall 56 (clone)")
    print("- _IO_file_open calls syscall 2 (open), syscall 3 (close), etc.")
    print()
    
    print("When a binary imports 'fopen':")
    print("1. We find 'fopen' in the imported functions")
    print("2. We look up 'fopen' in the call graph")
    print("3. We follow the call chain: fopen -> _IO_file_open -> syscall(2), syscall(3), etc.")
    print("4. We discover that fopen can trigger open, close, fstatat64 syscalls")

if __name__ == "__main__":
    demonstrate_indirect_syscall_discovery()
    show_real_call_graph_example()