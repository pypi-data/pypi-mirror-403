#!/usr/bin/env python3
"""
AlgoGraph CLI - Command-line interface for one-off graph operations.

Usage:
    algograph-shell [graph_file]           # Interactive mode
    algograph <command> <args> [graph_file] # One-off command
"""

import sys
import argparse
from .context import GraphContext
from .shell import GraphShell
from ..graph import Graph


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='AlgoGraph command-line interface',
        epilog='Use without arguments for interactive mode'
    )
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('-g', '--graph', help='Graph file to load (JSON)')

    args = parser.parse_args()

    # Load or create graph
    if args.graph:
        try:
            from ..serialization import load_graph
            print(f"Loading graph from {args.graph}...")
            graph = load_graph(args.graph)
            print(f"Loaded graph with {graph.vertex_count} vertices and {graph.edge_count} edges")
        except FileNotFoundError:
            print(f"Error: File '{args.graph}' not found", file=sys.stderr)
            print("Using sample graph instead.")
            graph = _create_sample_graph()
        except Exception as e:
            print(f"Error loading graph: {e}", file=sys.stderr)
            print("Using sample graph instead.")
            graph = _create_sample_graph()
    else:
        graph = _create_sample_graph()

    context = GraphContext(graph)

    # Interactive mode
    if args.command is None:
        shell = GraphShell(context)
        shell.run()
        return

    # One-off command mode
    shell = GraphShell(context)
    command_line = args.command + (' ' if args.args else '') + ' '.join(args.args)
    shell.execute_command(command_line)


def _create_sample_graph():
    """Create a sample graph."""
    from ..graph import Graph
    from ..vertex import Vertex
    from ..edge import Edge

    # Sample graph
    vertices = {
        Vertex('A', attrs={'value': 1}),
        Vertex('B', attrs={'value': 2}),
        Vertex('C', attrs={'value': 3}),
        Vertex('D', attrs={'value': 4}),
    }

    edges = {
        Edge('A', 'B', weight=1.0),
        Edge('A', 'C', weight=2.0),
        Edge('B', 'D', weight=1.0),
        Edge('C', 'D', weight=3.0),
    }

    return Graph(vertices, edges)


if __name__ == '__main__':
    main()
