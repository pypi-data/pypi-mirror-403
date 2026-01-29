"""
GraphContext - Immutable navigation state for graph shell.

Represents the current position in the graph and navigation mode.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from ..graph import Graph


@dataclass(frozen=True)
class GraphContext:
    """
    Immutable context representing navigation state in a graph.

    Attributes:
        graph: The graph being navigated
        current_vertex: Current vertex ID (like "current directory")
        mode: Navigation mode - 'vertex' or 'neighbors'
        attributes: Context-specific attributes (for output redirection, etc.)
    """
    graph: Graph
    current_vertex: Optional[str] = None
    mode: str = 'vertex'  # 'vertex' or 'neighbors'
    attributes: Dict[str, Any] = None

    def __post_init__(self):
        # Initialize attributes if None
        if self.attributes is None:
            object.__setattr__(self, 'attributes', {})

    def with_vertex(self, vertex_id: Optional[str]) -> 'GraphContext':
        """Navigate to a specific vertex."""
        return GraphContext(
            self.graph,
            vertex_id,
            mode='vertex',
            attributes=self.attributes
        )

    def with_neighbors_mode(self) -> 'GraphContext':
        """Enter neighbors mode for current vertex."""
        if self.current_vertex is None:
            raise ValueError("Cannot enter neighbors mode without a current vertex")
        return GraphContext(
            self.graph,
            self.current_vertex,
            mode='neighbors',
            attributes=self.attributes
        )

    def with_graph(self, graph: Graph) -> 'GraphContext':
        """Update the graph while maintaining current position."""
        # Validate current vertex still exists
        if self.current_vertex and not graph.has_vertex(self.current_vertex):
            return GraphContext(graph, None, 'vertex', self.attributes)
        return GraphContext(graph, self.current_vertex, self.mode, self.attributes)

    def with_attributes(self, **kwargs) -> 'GraphContext':
        """Add/update context attributes."""
        new_attrs = {**self.attributes, **kwargs}
        return GraphContext(self.graph, self.current_vertex, self.mode, new_attrs)

    def get_current_vertex(self):
        """Get the current vertex object."""
        if self.current_vertex is None:
            return None
        return self.graph.get_vertex(self.current_vertex)

    def get_neighbors(self):
        """Get neighbors of current vertex."""
        if self.current_vertex is None:
            return set()
        return self.graph.neighbors(self.current_vertex)

    def get_path(self) -> str:
        """Get current path (like pwd)."""
        if self.current_vertex is None:
            return "/"
        elif self.mode == 'neighbors':
            return f"/{self.current_vertex}/neighbors"
        else:
            return f"/{self.current_vertex}"

    def is_at_root(self) -> bool:
        """Check if at graph root (no current vertex)."""
        return self.current_vertex is None

    def is_in_neighbors_mode(self) -> bool:
        """Check if in neighbors viewing mode."""
        return self.mode == 'neighbors'
