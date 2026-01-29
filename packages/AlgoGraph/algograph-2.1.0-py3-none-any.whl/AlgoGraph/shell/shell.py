"""
GraphShell - Interactive REPL for graph navigation.
"""

import sys
import shlex
from typing import Dict, Type
from .context import GraphContext
from .commands import (
    Command, CommandResult,
    PwdCommand, LsCommand, CdCommand, InfoCommand,
    NeighborsCommand, FindCommand, PathCommand, ShortestCommand,
    ComponentsCommand, BfsCommand, SaveCommand, HelpCommand
)

# Try to import readline for command history and tab completion
try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False


class GraphShell:
    """Interactive shell for graph navigation."""

    def __init__(self, context: GraphContext):
        """
        Initialize shell with a graph context.

        Args:
            context: Initial GraphContext
        """
        self.context = context
        self.commands: Dict[str, Type[Command]] = {
            'pwd': PwdCommand,
            'ls': LsCommand,
            'cd': CdCommand,
            'info': InfoCommand,
            'neighbors': NeighborsCommand,
            'find': FindCommand,
            'path': PathCommand,
            'shortest': ShortestCommand,
            'components': ComponentsCommand,
            'bfs': BfsCommand,
            'save': SaveCommand,
            'help': HelpCommand,
        }

        # Set up readline for command history and tab completion
        if HAS_READLINE:
            self._setup_readline()

    def _setup_readline(self):
        """Set up readline for command history and tab completion."""
        # Enable tab completion
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._completer)

        # Set completer delimiters (exclude '/' so we can complete paths)
        readline.set_completer_delims(' \t\n')

    def _completer(self, text: str, state: int):
        """
        Tab completion handler.

        Completes commands and vertex names based on context.
        """
        # Get the current line
        line = readline.get_line_buffer()
        parts = line.split()

        # If we're at the start, complete command names
        if not parts or (len(parts) == 1 and not line.endswith(' ')):
            commands = list(self.commands.keys()) + ['exit', 'quit', 'q']
            matches = [cmd for cmd in commands if cmd.startswith(text)]
        else:
            # Complete vertex names or special keywords
            cmd_name = parts[0]

            # Get available completions based on context
            completions = []

            # Special keywords
            if cmd_name == 'cd':
                completions.extend(['..', '/', 'neighbors'])

            # Vertex names (always available)
            if self.context.is_at_root() or not self.context.is_in_neighbors_mode():
                # Can complete any vertex name
                completions.extend([v.id for v in self.context.graph.vertices])
            elif self.context.is_in_neighbors_mode():
                # Can only complete neighbor names
                completions.extend(self.context.get_neighbors())

            matches = [c for c in completions if c.startswith(text)]

        # Return the match at the requested state
        if state < len(matches):
            return matches[state]
        return None

    def get_prompt(self) -> str:
        """Get the shell prompt."""
        path = self.context.get_path()
        vertex_count = self.context.graph.vertex_count
        return f"graph({vertex_count}v):{path}$ "

    def execute_command(self, line: str) -> bool:
        """
        Execute a command line.

        Args:
            line: Command line to execute

        Returns:
            True to continue, False to exit
        """
        line = line.strip()

        # Empty line
        if not line:
            return True

        # Exit commands
        if line in ('exit', 'quit', 'q'):
            return False

        # Parse command using shlex for proper quote handling
        try:
            parts = shlex.split(line)
        except ValueError as e:
            print(f"Error parsing command: {e}", file=sys.stderr)
            return True

        if not parts:
            return True

        cmd_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Check if command exists
        if cmd_name not in self.commands:
            print(f"Unknown command: {cmd_name}")
            print("Type 'help' for available commands")
            return True

        # Execute command
        try:
            command = self.commands[cmd_name]()
            result = command.execute(self.context, args)

            # Update context
            self.context = result.context

            # Show output
            if result.output:
                print(result.output)

            # Show error if any
            if not result.success and result.error:
                print(f"Error: {result.error}", file=sys.stderr)

        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)

        return True

    def run(self):
        """Run the interactive shell."""
        print("AlgoGraph Shell")
        print("Type 'help' for available commands, 'exit' to quit")
        print()

        # Show initial status
        if self.context.graph.vertex_count == 0:
            print("Warning: Graph is empty")
        else:
            print(f"Graph loaded: {self.context.graph.vertex_count} vertices, "
                  f"{self.context.graph.edge_count} edges")
        print()

        while True:
            try:
                # Get input
                prompt = self.get_prompt()
                line = input(prompt)

                # Execute
                if not self.execute_command(line):
                    print("Goodbye!")
                    break

            except EOFError:
                print("\nGoodbye!")
                break
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
                continue


def main():
    """Entry point for interactive shell."""
    import argparse
    from ..serialization import load_graph

    parser = argparse.ArgumentParser(description='AlgoGraph interactive shell')
    parser.add_argument('graph_file', nargs='?', help='Graph file to load (JSON)')
    args = parser.parse_args()

    # Create or load graph
    if args.graph_file:
        try:
            print(f"Loading graph from {args.graph_file}...")
            graph = load_graph(args.graph_file)
            print(f"Loaded graph with {graph.vertex_count} vertices and {graph.edge_count} edges")
        except FileNotFoundError:
            print(f"Error: File '{args.graph_file}' not found", file=sys.stderr)
            print("Using sample graph instead.")
            graph = _create_sample_graph()
        except Exception as e:
            print(f"Error loading graph: {e}", file=sys.stderr)
            print("Using sample graph instead.")
            graph = _create_sample_graph()
    else:
        graph = _create_sample_graph()

    # Create context and run shell
    context = GraphContext(graph)
    shell = GraphShell(context)
    shell.run()


def _create_sample_graph():
    """Create a sample graph for demo purposes."""
    from ..graph import Graph
    from ..vertex import Vertex
    from ..edge import Edge

    # Sample social network
    vertices = {
        Vertex('Alice', attrs={'age': 30, 'city': 'NYC'}),
        Vertex('Bob', attrs={'age': 25, 'city': 'Boston'}),
        Vertex('Charlie', attrs={'age': 35, 'city': 'NYC'}),
        Vertex('Diana', attrs={'age': 28, 'city': 'Seattle'}),
        Vertex('Eve', attrs={'age': 32, 'city': 'Boston'}),
    }

    edges = {
        Edge('Alice', 'Bob', directed=False),
        Edge('Alice', 'Charlie', directed=False),
        Edge('Bob', 'Diana', directed=False),
        Edge('Charlie', 'Diana', directed=False),
        Edge('Diana', 'Eve', directed=False),
    }

    return Graph(vertices, edges)


if __name__ == '__main__':
    main()
