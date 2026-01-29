"""
Core shell commands for graph navigation.
"""

from dataclasses import dataclass
from typing import List, Optional
from .context import GraphContext
from ..algorithms.traversal import find_path, bfs
from ..algorithms.shortest_path import shortest_path, shortest_path_length
from ..algorithms.connectivity import connected_components, is_connected


@dataclass
class CommandResult:
    """Result of executing a command."""
    success: bool
    output: str
    context: GraphContext
    error: Optional[str] = None


class Command:
    """Base class for shell commands."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        """Execute the command."""
        raise NotImplementedError


class PwdCommand(Command):
    """Print working directory (current vertex path)."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        path = context.get_path()
        return CommandResult(
            success=True,
            output=path,
            context=context
        )


class LsCommand(Command):
    """
    List contents of current location.

    - At root (/): Shows all vertices
    - At vertex: Shows attributes and 'neighbors/' pseudo-directory
    - In neighbors mode: Shows neighboring vertices
    """

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        lines = []

        if context.is_at_root():
            # At root - show all vertices
            vertices = sorted([v.id for v in context.graph.vertices])
            if not vertices:
                lines.append("(empty graph)")
            else:
                for vid in vertices:
                    v = context.graph.get_vertex(vid)
                    degree = context.graph.degree(vid)
                    lines.append(f"{vid}/  [{degree} neighbors]")

        elif context.is_in_neighbors_mode():
            # In neighbors mode - show neighbors
            neighbors = sorted(context.get_neighbors())
            if not neighbors:
                lines.append("(no neighbors)")
            else:
                for neighbor_id in neighbors:
                    # Get edge info if available
                    edge = context.graph.get_edge(context.current_vertex, neighbor_id)
                    if edge:
                        weight_str = f" [weight: {edge.weight}]" if edge.weight != 1.0 else ""
                        direction = "->" if edge.directed else "<->"
                        lines.append(f"{neighbor_id}/  {direction}{weight_str}")
                    else:
                        lines.append(f"{neighbor_id}/")

        else:
            # At vertex - show attributes and neighbors/
            vertex = context.get_current_vertex()
            if vertex is None:
                return CommandResult(
                    success=False,
                    output="",
                    context=context,
                    error="Current vertex not found"
                )

            # Show attributes
            if vertex.attrs:
                lines.append("Attributes:")
                for key, value in sorted(vertex.attrs.items()):
                    lines.append(f"  {key} = {value}")
            else:
                lines.append("(no attributes)")

            # Show neighbors pseudo-directory
            neighbor_count = len(context.get_neighbors())
            lines.append("")
            lines.append(f"neighbors/  [{neighbor_count} vertices]")

        return CommandResult(
            success=True,
            output="\n".join(lines),
            context=context
        )


class CdCommand(Command):
    """
    Change directory - navigate to a vertex or special location.

    Usage:
        cd <vertex>     - Navigate to vertex
        cd /vertex      - Navigate to vertex (absolute path)
        cd neighbors    - Enter neighbors mode
        cd ..           - Go up one level
        cd /            - Go to root
        cd              - Go to root
    """

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        if not args or args[0] == '/':
            # Go to root
            new_context = context.with_vertex(None)
            return CommandResult(
                success=True,
                output=f"Now at: {new_context.get_path()}",
                context=new_context
            )

        target = args[0]

        # Handle absolute paths (starts with /)
        if target.startswith('/') and target != '/':
            # Absolute path - strip leading / and navigate to that vertex
            vertex_id = target[1:]
            if not context.graph.has_vertex(vertex_id):
                return CommandResult(
                    success=False,
                    output="",
                    context=context,
                    error=f"Vertex '{vertex_id}' not found in graph"
                )
            new_context = context.with_vertex(vertex_id)
            return CommandResult(
                success=True,
                output=f"Now at: {new_context.get_path()}",
                context=new_context
            )

        # Handle special cases
        if target == '..':
            # Go up one level
            if context.is_in_neighbors_mode():
                # From neighbors mode -> back to vertex
                new_context = context.with_vertex(context.current_vertex)
            elif context.current_vertex is not None:
                # From vertex -> root
                new_context = context.with_vertex(None)
            else:
                # Already at root
                return CommandResult(
                    success=False,
                    output="",
                    context=context,
                    error="Already at root"
                )
            return CommandResult(
                success=True,
                output=f"Now at: {new_context.get_path()}",
                context=new_context
            )

        if target == 'neighbors':
            # Enter neighbors mode
            if context.current_vertex is None:
                return CommandResult(
                    success=False,
                    output="",
                    context=context,
                    error="Cannot view neighbors from root. Navigate to a vertex first."
                )
            new_context = context.with_neighbors_mode()
            return CommandResult(
                success=True,
                output=f"Now at: {new_context.get_path()}",
                context=new_context
            )

        # Navigate to a vertex
        if context.is_in_neighbors_mode():
            # In neighbors mode - can only cd to neighbors
            if target not in context.get_neighbors():
                return CommandResult(
                    success=False,
                    output="",
                    context=context,
                    error=f"'{target}' is not a neighbor of {context.current_vertex}"
                )
            new_context = context.with_vertex(target)
        else:
            # In normal mode - can cd to any vertex
            if not context.graph.has_vertex(target):
                return CommandResult(
                    success=False,
                    output="",
                    context=context,
                    error=f"Vertex '{target}' not found in graph"
                )
            new_context = context.with_vertex(target)

        return CommandResult(
            success=True,
            output=f"Now at: {new_context.get_path()}",
            context=new_context
        )


class InfoCommand(Command):
    """Show information about current vertex or the graph."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        lines = []

        if context.is_at_root():
            # Show graph info
            lines.append("Graph Information:")
            lines.append(f"  Vertices: {context.graph.vertex_count}")
            lines.append(f"  Edges: {context.graph.edge_count}")

            # Count directed vs undirected
            directed = sum(1 for e in context.graph.edges if e.directed)
            undirected = context.graph.edge_count - directed
            if directed > 0 and undirected > 0:
                lines.append(f"  Directed edges: {directed}")
                lines.append(f"  Undirected edges: {undirected}")
            elif directed > 0:
                lines.append("  Type: Directed")
            elif undirected > 0:
                lines.append("  Type: Undirected")

        else:
            # Show vertex info
            vertex = context.get_current_vertex()
            if vertex is None:
                return CommandResult(
                    success=False,
                    output="",
                    context=context,
                    error="Current vertex not found"
                )

            lines.append(f"Vertex: {vertex.id}")
            lines.append(f"Degree: {context.graph.degree(vertex.id)}")

            in_degree = context.graph.in_degree(vertex.id)
            out_degree = context.graph.out_degree(vertex.id)
            if in_degree != out_degree:
                lines.append(f"In-degree: {in_degree}")
                lines.append(f"Out-degree: {out_degree}")

            if vertex.attrs:
                lines.append("\nAttributes:")
                for key, value in sorted(vertex.attrs.items()):
                    lines.append(f"  {key} = {value}")

        return CommandResult(
            success=True,
            output="\n".join(lines),
            context=context
        )


class NeighborsCommand(Command):
    """Show neighbors of current vertex (alternative to cd neighbors + ls)."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        if context.current_vertex is None:
            return CommandResult(
                success=False,
                output="",
                context=context,
                error="Not at a vertex. Navigate to a vertex first."
            )

        neighbors = sorted(context.get_neighbors())
        lines = []

        if not neighbors:
            lines.append(f"{context.current_vertex} has no neighbors")
        else:
            lines.append(f"Neighbors of {context.current_vertex}:")
            for neighbor_id in neighbors:
                edge = context.graph.get_edge(context.current_vertex, neighbor_id)
                if edge:
                    weight_str = f" (weight: {edge.weight})" if edge.weight != 1.0 else ""
                    direction = "->" if edge.directed else "<->"
                    lines.append(f"  {neighbor_id} {direction}{weight_str}")
                else:
                    lines.append(f"  {neighbor_id}")

        return CommandResult(
            success=True,
            output="\n".join(lines),
            context=context
        )


class FindCommand(Command):
    """Find a vertex in the graph."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(
                success=False,
                output="",
                context=context,
                error="Usage: find <vertex>"
            )

        vertex_id = args[0]

        if context.graph.has_vertex(vertex_id):
            vertex = context.graph.get_vertex(vertex_id)
            lines = [
                f"Found: {vertex_id}",
                f"Degree: {context.graph.degree(vertex_id)}"
            ]
            if vertex.attrs:
                lines.append("Attributes:")
                for key, value in sorted(vertex.attrs.items()):
                    lines.append(f"  {key} = {value}")

            return CommandResult(
                success=True,
                output="\n".join(lines),
                context=context
            )
        else:
            return CommandResult(
                success=False,
                output="",
                context=context,
                error=f"Vertex '{vertex_id}' not found"
            )


class PathCommand(Command):
    """Find any path between two vertices."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(
                success=False,
                output="",
                context=context,
                error="Usage: path <start> <end>"
            )

        start, end = args[0], args[1]

        if not context.graph.has_vertex(start):
            return CommandResult(
                success=False,
                output="",
                context=context,
                error=f"Start vertex '{start}' not found"
            )

        if not context.graph.has_vertex(end):
            return CommandResult(
                success=False,
                output="",
                context=context,
                error=f"End vertex '{end}' not found"
            )

        path = find_path(context.graph, start, end)

        if path:
            path_str = " -> ".join(path)
            return CommandResult(
                success=True,
                output=f"Path found: {path_str}\nLength: {len(path) - 1} edges",
                context=context
            )
        else:
            return CommandResult(
                success=True,
                output=f"No path exists from {start} to {end}",
                context=context
            )


class ShortestCommand(Command):
    """Find shortest path between two vertices."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(
                success=False,
                output="",
                context=context,
                error="Usage: shortest <start> <end>"
            )

        start, end = args[0], args[1]

        if not context.graph.has_vertex(start):
            return CommandResult(
                success=False,
                output="",
                context=context,
                error=f"Start vertex '{start}' not found"
            )

        if not context.graph.has_vertex(end):
            return CommandResult(
                success=False,
                output="",
                context=context,
                error=f"End vertex '{end}' not found"
            )

        path = shortest_path(context.graph, start, end)

        if path:
            path_str = " -> ".join(path)
            length = shortest_path_length(context.graph, start, end)
            return CommandResult(
                success=True,
                output=f"Shortest path: {path_str}\nDistance: {length}",
                context=context
            )
        else:
            return CommandResult(
                success=True,
                output=f"No path exists from {start} to {end}",
                context=context
            )


class ComponentsCommand(Command):
    """Show connected components of the graph."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        components = connected_components(context.graph)

        lines = [f"Connected components: {len(components)}"]
        lines.append("")

        for i, component in enumerate(components, 1):
            vertices = sorted(component)
            lines.append(f"Component {i} ({len(vertices)} vertices):")
            lines.append("  " + ", ".join(vertices))

        return CommandResult(
            success=True,
            output="\n".join(lines),
            context=context
        )


class BfsCommand(Command):
    """Perform breadth-first search from current vertex or specified vertex."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        if args:
            start = args[0]
        elif context.current_vertex:
            start = context.current_vertex
        else:
            return CommandResult(
                success=False,
                output="",
                context=context,
                error="Usage: bfs [start_vertex] or navigate to a vertex first"
            )

        if not context.graph.has_vertex(start):
            return CommandResult(
                success=False,
                output="",
                context=context,
                error=f"Vertex '{start}' not found"
            )

        order = bfs(context.graph, start)
        levels_str = " -> ".join(order)

        return CommandResult(
            success=True,
            output=f"BFS from {start}:\n{levels_str}\n\nVisited {len(order)} vertices",
            context=context
        )


class SaveCommand(Command):
    """Save current graph to a JSON file."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        if not args:
            return CommandResult(
                success=False,
                output="",
                context=context,
                error="Usage: save <filename>"
            )

        filename = args[0]

        try:
            from ..serialization import save_graph
            save_graph(context.graph, filename)
            return CommandResult(
                success=True,
                output=f"Graph saved to {filename}",
                context=context
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                context=context,
                error=f"Failed to save graph: {e}"
            )


class HelpCommand(Command):
    """Show help information."""

    def execute(self, context: GraphContext, args: List[str]) -> CommandResult:
        help_text = """
AlgoGraph Shell Commands:

Navigation:
  cd <vertex>     - Navigate to a vertex (relative)
  cd /vertex      - Navigate to a vertex (absolute path)
  cd neighbors    - View neighbors of current vertex
  cd ..           - Go up one level
  cd / or cd      - Go to root
  ls              - List contents of current location
  pwd             - Print current path

Information:
  info            - Show info about current vertex or graph
  neighbors       - Show neighbors of current vertex
  help            - Show this help message

Graph Queries:
  find <vertex>   - Find vertex in graph
  path <v1> <v2>  - Find path between vertices
  shortest <v1> <v2> - Find shortest path (weighted)
  components      - Show connected components
  bfs [start]     - Breadth-first search from vertex

File Operations:
  save <file>     - Save graph to JSON file

Other:
  exit, quit      - Exit the shell

Tips:
  - Use quotes for vertex names with spaces: cd "Alice Smith"
  - Press TAB for command/vertex name completion
  - Use UP/DOWN arrows for command history
"""
        return CommandResult(
            success=True,
            output=help_text.strip(),
            context=context
        )
