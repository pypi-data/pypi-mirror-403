"""
Graph builder for fluent graph construction.

Provides a fluent API for building graphs with less verbosity.
"""

from typing import Any, Dict, Set, List, Optional, Tuple, Union
from .graph import Graph
from .vertex import Vertex
from .edge import Edge


class GraphBuilder:
    """
    Fluent builder for constructing graphs.

    Provides a chainable API that reduces verbosity for graph construction.

    Example:
        >>> g = (GraphBuilder()
        ...      .add_vertex('A', value=1)
        ...      .add_vertex('B', value=2)
        ...      .add_edge('A', 'B', weight=5)
        ...      .build())
        >>> g.has_vertex('A')
        True
    """

    def __init__(self):
        """Initialize an empty builder."""
        self._vertices: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Tuple[str, str, bool, float, Dict[str, Any]]] = []

    def add_vertex(self, vertex_id: str, **attrs) -> 'GraphBuilder':
        """
        Add a vertex with optional attributes.

        Args:
            vertex_id: Unique identifier for the vertex
            **attrs: Arbitrary attributes for the vertex

        Returns:
            Self for chaining

        Example:
            >>> builder = GraphBuilder().add_vertex('A', value=10, color='red')
        """
        self._vertices[vertex_id] = attrs
        return self

    def add_vertices(self, *vertex_ids: str, **common_attrs) -> 'GraphBuilder':
        """
        Add multiple vertices with optional common attributes.

        Args:
            *vertex_ids: Variable number of vertex IDs
            **common_attrs: Attributes to apply to all vertices

        Returns:
            Self for chaining

        Example:
            >>> builder = GraphBuilder().add_vertices('A', 'B', 'C', layer=1)
        """
        for vid in vertex_ids:
            self._vertices[vid] = common_attrs.copy()
        return self

    def add_edge(
        self,
        source: str,
        target: str,
        *,
        directed: bool = True,
        weight: float = 1.0,
        **attrs
    ) -> 'GraphBuilder':
        """
        Add an edge between vertices.

        Args:
            source: Source vertex ID
            target: Target vertex ID
            directed: Whether edge is directed (default: True)
            weight: Edge weight (default: 1.0)
            **attrs: Arbitrary edge attributes

        Returns:
            Self for chaining

        Example:
            >>> builder = (GraphBuilder()
            ...            .add_edge('A', 'B', weight=5, label='connection'))
        """
        # Auto-create vertices if they don't exist
        if source not in self._vertices:
            self._vertices[source] = {}
        if target not in self._vertices:
            self._vertices[target] = {}

        self._edges.append((source, target, directed, weight, attrs))
        return self

    def add_edges(
        self,
        *edges: Tuple[str, str],
        directed: bool = True,
        weight: float = 1.0,
        **common_attrs
    ) -> 'GraphBuilder':
        """
        Add multiple edges with common properties.

        Args:
            *edges: Variable number of (source, target) tuples
            directed: Whether edges are directed (default: True)
            weight: Common weight for all edges (default: 1.0)
            **common_attrs: Common attributes for all edges

        Returns:
            Self for chaining

        Example:
            >>> builder = (GraphBuilder()
            ...            .add_edges(('A', 'B'), ('B', 'C'), ('C', 'D'),
            ...                      directed=False))
        """
        for source, target in edges:
            self.add_edge(source, target, directed=directed, weight=weight, **common_attrs)
        return self

    def add_path(
        self,
        *vertices: str,
        directed: bool = True,
        weight: float = 1.0,
        **edge_attrs
    ) -> 'GraphBuilder':
        """
        Add a path through vertices.

        Creates edges: v1->v2, v2->v3, ..., vn-1->vn

        Args:
            *vertices: Vertices in path order
            directed: Whether edges are directed (default: True)
            weight: Weight for all edges (default: 1.0)
            **edge_attrs: Common attributes for all edges

        Returns:
            Self for chaining

        Example:
            >>> builder = GraphBuilder().add_path('A', 'B', 'C', 'D', directed=False)
        """
        if len(vertices) == 0:
            return self

        if len(vertices) == 1:
            # Add single vertex with no edges
            self.add_vertex(vertices[0])
            return self

        for i in range(len(vertices) - 1):
            self.add_edge(vertices[i], vertices[i + 1],
                         directed=directed, weight=weight, **edge_attrs)
        return self

    def add_cycle(
        self,
        *vertices: str,
        directed: bool = True,
        weight: float = 1.0,
        **edge_attrs
    ) -> 'GraphBuilder':
        """
        Add a cycle through vertices.

        Creates edges: v1->v2, v2->v3, ..., vn->v1

        Args:
            *vertices: Vertices in cycle order
            directed: Whether edges are directed (default: True)
            weight: Weight for all edges (default: 1.0)
            **edge_attrs: Common attributes for all edges

        Returns:
            Self for chaining

        Example:
            >>> builder = GraphBuilder().add_cycle('A', 'B', 'C', directed=True)
        """
        if len(vertices) < 2:
            return self

        # Add path through vertices
        self.add_path(*vertices, directed=directed, weight=weight, **edge_attrs)
        # Close the cycle
        self.add_edge(vertices[-1], vertices[0],
                     directed=directed, weight=weight, **edge_attrs)
        return self

    def add_complete(
        self,
        *vertices: str,
        directed: bool = False,
        weight: float = 1.0,
        **edge_attrs
    ) -> 'GraphBuilder':
        """
        Add a complete graph (clique) on vertices.

        Connects every pair of vertices.

        Args:
            *vertices: Vertices to connect
            directed: Whether edges are directed (default: False for cliques)
            weight: Weight for all edges (default: 1.0)
            **edge_attrs: Common attributes for all edges

        Returns:
            Self for chaining

        Example:
            >>> builder = GraphBuilder().add_complete('A', 'B', 'C', 'D')
        """
        vertices_list = list(vertices)
        for i, source in enumerate(vertices_list):
            for target in vertices_list[i + 1:]:
                self.add_edge(source, target, directed=False, weight=weight, **edge_attrs)
                if directed:
                    self.add_edge(target, source, directed=True, weight=weight, **edge_attrs)
        return self

    def add_star(
        self,
        center: str,
        *satellites: str,
        directed: bool = False,
        weight: float = 1.0,
        **edge_attrs
    ) -> 'GraphBuilder':
        """
        Add a star graph with center connected to all satellites.

        Args:
            center: Central vertex ID
            *satellites: Satellite vertex IDs
            directed: Whether edges are directed from center (default: False)
            weight: Weight for all edges (default: 1.0)
            **edge_attrs: Common attributes for all edges

        Returns:
            Self for chaining

        Example:
            >>> builder = GraphBuilder().add_star('Hub', 'A', 'B', 'C', 'D')
        """
        for satellite in satellites:
            self.add_edge(center, satellite, directed=directed, weight=weight, **edge_attrs)
            if not directed:
                # For undirected, we only add once (handled in add_edge)
                pass
        return self

    def add_bipartite(
        self,
        left: List[str],
        right: List[str],
        *,
        complete: bool = False,
        directed: bool = False,
        weight: float = 1.0,
        **edge_attrs
    ) -> 'GraphBuilder':
        """
        Add bipartite graph structure.

        Args:
            left: Left partition vertex IDs
            right: Right partition vertex IDs
            complete: If True, add all edges between partitions (default: False)
            directed: Whether edges are directed (default: False)
            weight: Weight for all edges (default: 1.0)
            **edge_attrs: Common attributes for all edges

        Returns:
            Self for chaining

        Example:
            >>> builder = (GraphBuilder()
            ...            .add_bipartite(['A', 'B'], ['X', 'Y', 'Z'], complete=True))
        """
        # Add all vertices
        for vid in left:
            if vid not in self._vertices:
                self._vertices[vid] = {'partition': 'left'}
        for vid in right:
            if vid not in self._vertices:
                self._vertices[vid] = {'partition': 'right'}

        # Add edges if complete
        if complete:
            for l in left:
                for r in right:
                    self.add_edge(l, r, directed=directed, weight=weight, **edge_attrs)

        return self

    def build(self) -> Graph:
        """
        Build the graph from accumulated vertices and edges.

        Returns:
            Constructed Graph

        Example:
            >>> g = GraphBuilder().add_vertex('A').add_edge('A', 'B').build()
        """
        # Create vertex objects
        vertices = {Vertex(vid, attrs=attrs) for vid, attrs in self._vertices.items()}

        # Create edge objects
        edges = {
            Edge(source, target, directed=directed, weight=weight, attrs=attrs)
            for source, target, directed, weight, attrs in self._edges
        }

        return Graph(vertices, edges)

    def __repr__(self) -> str:
        """String representation."""
        return f"GraphBuilder(vertices={len(self._vertices)}, edges={len(self._edges)})"
