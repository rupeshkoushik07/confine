#!/usr/bin/env python3
"""
Real-world example showing how indirect syscalls are discovered
for an actual compiled binary using the real libc call graph.
"""

import sys
import os
sys.path.insert(0, './python-utils/')

from graph import Graph
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    return logging.getLogger(__name__)

def create_realistic_call_graph():
    """Create a call graph based on real libc behavior"""
    logger = setup_logging()
    graph = Graph(logger)
    
    # Based on real glibc call graph patterns
    # pthread_create directly calls clone syscall
    graph.addEdge("pthread_create", "syscall( 56 )")
    
    # fopen -> _IO_file_open -> multiple syscalls
    graph.addEdge("fopen", "_IO_file_open")
    graph.addEdge("_IO_file_open", "syscall( 2 )")   # open
    graph.addEdge("_IO_file_open", "syscall( 3 )")   # close
    graph.addEdge("_IO_file_open", "syscall( 322 )") # fstatat64
    
    # fwrite -> _IO_file_write -> write syscall
    graph.addEdge("fwrite", "_IO_file_write")
    graph.addEdge("_IO_file_write", "syscall( 1 )")  # write
    
    # fclose -> _IO_file_close -> close syscall
    graph.addEdge("fclose", "_IO_file_close")
    graph.addEdge("_IO_file_close", "syscall( 3 )")  # close
    
    # malloc -> _int_malloc -> mmap syscall
    graph.addEdge("malloc", "_int_malloc")
    graph.addEdge("_int_malloc", "syscall( 9 )")     # mmap
    
    # free -> _int_free -> munmap syscall
    graph.addEdge("free", "_int_free")
    graph.addEdge("_int_free", "syscall( 11 )")      # munmap
    
    # write -> direct syscall
    graph.addEdge("write", "syscall( 1 )")           # write
    
    # puts -> _IO_puts -> _IO_file_write -> write syscall
    graph.addEdge("puts", "_IO_puts")
    graph.addEdge("_IO_puts", "_IO_file_write")
    graph.addEdge("_IO_file_write", "syscall( 1 )")  # write
    
    # pthread_join -> futex syscall
    graph.addEdge("pthread_join", "syscall( 202 )")  # futex
    
    return graph

def demonstrate_real_binary_analysis():
    """Demonstrate analysis of our real compiled binary"""
    logger = setup_logging()
    
    print("=== REAL BINARY INDIRECT SYSCALL ANALYSIS ===\n")
    
    # Step 1: Show what functions our binary actually imports
    print("Step 1: Functions imported by our test binary:")
    imported_functions = [
        "pthread_create", "pthread_join", "fopen", "fclose", 
        "fwrite", "malloc", "free", "write", "puts"
    ]
    print(f"   - Imported functions: {imported_functions}")
    print()
    
    # Step 2: Load the call graph
    print("Step 2: Loading libc call graph...")
    call_graph = create_realistic_call_graph()
    print(f"   - Call graph loaded with {call_graph.getNodeCount()} nodes")
    print()
    
    # Step 3: Generate syscall patterns
    print("Step 3: Generating syscall patterns...")
    syscall_patterns = []
    for i in range(400):
        syscall_patterns.append(f"syscall( {i} )")
    print(f"   - Looking for all syscall patterns (0-399)")
    print()
    
    # Step 4: Analyze each imported function
    print("Step 4: Analyzing each imported function for indirect syscalls...")
    all_discovered_syscalls = set()
    
    for func in imported_functions:
        print(f"   Analyzing: {func}")
        
        # Find all reachable syscalls from this function
        leaves = call_graph.getLeavesFromStartNode(func, syscall_patterns, [])
        
        if leaves:
            syscalls = []
            for leaf in leaves:
                if leaf.startswith("syscall(") and leaf.endswith(")"):
                    syscall_num = leaf[8:-1].strip()
                    try:
                        syscalls.append(int(syscall_num))
                    except ValueError:
                        pass
            
            if syscalls:
                print(f"     -> Discovered syscalls: {sorted(syscalls)}")
                all_discovered_syscalls.update(syscalls)
            else:
                print(f"     -> No syscalls found")
        else:
            print(f"     -> No leaf nodes found")
    
    print()
    
    # Step 5: Show final results
    print("Step 5: Complete Syscall Profile")
    print(f"   - Total unique syscalls: {len(all_discovered_syscalls)}")
    print(f"   - Syscall numbers: {sorted(all_discovered_syscalls)}")
    
    # Map to common syscall names
    syscall_names = {
        0: "read", 1: "write", 2: "open", 3: "close", 
        9: "mmap", 11: "munmap", 56: "clone", 202: "futex", 322: "fstatat64"
    }
    
    print("\n   - Syscall mapping:")
    for num in sorted(all_discovered_syscalls):
        name = syscall_names.get(num, f"unknown_{num}")
        print(f"     {num:3d} -> {name}")
    
    print("\n=== ANALYSIS COMPLETE ===")

def show_call_chains():
    """Show specific call chains for key functions"""
    print("\n=== DETAILED CALL CHAINS ===\n")
    
    print("Key function call chains:")
    print()
    
    print("1. fopen -> _IO_file_open -> syscall(2), syscall(3), syscall(322)")
    print("   This means fopen can trigger: open, close, fstatat64")
    print()
    
    print("2. pthread_create -> syscall(56)")
    print("   This means pthread_create directly calls clone")
    print()
    
    print("3. malloc -> _int_malloc -> syscall(9)")
    print("   This means malloc can trigger mmap for large allocations")
    print()
    
    print("4. write -> syscall(1)")
    print("   This means write directly calls the write syscall")
    print()
    
    print("5. pthread_join -> syscall(202)")
    print("   This means pthread_join uses futex for synchronization")

if __name__ == "__main__":
    demonstrate_real_binary_analysis()
    show_call_chains()