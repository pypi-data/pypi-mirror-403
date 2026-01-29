"""
Immutable Graph implementation.

Provides a container for vertices and edges with graph operations and algorithms.
"""

from typing import Set, Dict, List, Optional, Callable, Any, Tuple, Iterator
from dataclasses import dataclass, field
from collections import defaultdict

from .vertex import Vertex
from .edge import Edge


@dataclass(frozen=True)
class Graph:
    """
    Immutable graph container.

    Stores vertices and edges with efficient lookup structures.
    Supports both directed and undirected graphs (or mixed).

    Attributes:
        vertices: Set of Vertex objects
        edges: Set of Edge objects
        _adj: Adjacency list (computed lazily)

    Example:
        >>> v1, v2, v3 = Vertex('A'), Vertex('B'), Vertex('C')
        >>> e1 = Edge('A', 'B', weight=2.0)
        >>> e2 = Edge('B', 'C', weight=3.0)
        >>> g = Graph({v1, v2, v3}, {e1, e2})
        >>> g.has_vertex('A')
        True
        >>> g.degree('A')
        1
    """

    vertices: Set[Vertex] = field(default_factory=set)
    edges: Set[Edge] = field(default_factory=set)

    def __post_init__(self):
        """Ensure vertices and edges are sets and build vertex index."""
        if not isinstance(self.vertices, set):
            object.__setattr__(self, 'vertices', set(self.vertices))
        if not isinstance(self.edges, set):
            object.__setattr__(self, 'edges', set(self.edges))
        # Build vertex index for O(1) lookup by ID
        object.__setattr__(self, '_vertex_by_id',
                           {v.id: v for v in self.vertices})

    @classmethod
    def builder(cls) -> 'GraphBuilder':
        """
        Create a GraphBuilder for fluent graph construction.

        Returns:
            New GraphBuilder instance

        Example:
            >>> g = (Graph.builder()
            ...      .add_vertex('A', value=1)
            ...      .add_edge('A', 'B', weight=5)
            ...      .build())
        """
        from .builder import GraphBuilder
        return GraphBuilder()

    @classmethod
    def from_edges(cls, *edges: Tuple[str, str], directed: bool = True, weight: float = 1.0) -> 'Graph':
        """
        Create graph from list of edge tuples.

        Args:
            *edges: Variable number of (source, target) tuples
            directed: Whether edges are directed (default: True)
            weight: Weight for all edges (default: 1.0)

        Returns:
            New Graph

        Example:
            >>> g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'A'))
            >>> g.vertex_count
            3
        """
        from .builder import GraphBuilder
        builder = GraphBuilder()
        for source, target in edges:
            builder.add_edge(source, target, directed=directed, weight=weight)
        return builder.build()

    @classmethod
    def from_vertices(cls, *vertex_ids: str, **common_attrs) -> 'Graph':
        """
        Create graph from list of vertex IDs.

        Args:
            *vertex_ids: Variable number of vertex IDs
            **common_attrs: Attributes to apply to all vertices

        Returns:
            New Graph with no edges

        Example:
            >>> g = Graph.from_vertices('A', 'B', 'C', layer=1)
            >>> g.vertex_count
            3
        """
        vertices = {Vertex(vid, attrs=common_attrs) for vid in vertex_ids}
        return cls(vertices, set())

    @property
    def vertex_count(self) -> int:
        """Get number of vertices."""
        return len(self.vertices)

    @property
    def edge_count(self) -> int:
        """Get number of edges."""
        return len(self.edges)

    @property
    def is_directed(self) -> bool:
        """Check if all edges are directed."""
        return all(e.directed for e in self.edges)

    @property
    def is_undirected(self) -> bool:
        """Check if all edges are undirected."""
        return all(not e.directed for e in self.edges)

    def get_vertex(self, vertex_id: str) -> Optional[Vertex]:
        """
        Get vertex by ID.

        Args:
            vertex_id: Vertex ID to find

        Returns:
            Vertex if found, None otherwise

        Example:
            >>> g = Graph({Vertex('A'), Vertex('B')})
            >>> v = g.get_vertex('A')
            >>> v.id
            'A'
        """
        return self._vertex_by_id.get(vertex_id)

    def has_vertex(self, vertex_id: str) -> bool:
        """Check if vertex exists in graph."""
        return vertex_id in self._vertex_by_id

    def has_edge(self, source: str, target: str) -> bool:
        """
        Check if edge exists between vertices.

        For undirected graphs, checks both directions.

        Args:
            source: Source vertex ID
            target: Target vertex ID

        Returns:
            True if edge exists

        Example:
            >>> e = Edge('A', 'B', directed=False)
            >>> g = Graph(edges={e})
            >>> g.has_edge('A', 'B')
            True
            >>> g.has_edge('B', 'A')
            True
        """
        for e in self.edges:
            if e.connects(source, target):
                return True
        return False

    def get_edge(self, source: str, target: str) -> Optional[Edge]:
        """
        Get edge between vertices.

        Args:
            source: Source vertex ID
            target: Target vertex ID

        Returns:
            Edge if found, None otherwise
        """
        for e in self.edges:
            if e.connects(source, target):
                return e
        return None

    def neighbors(self, vertex_id: str) -> Set[str]:
        """
        Get neighboring vertex IDs.

        For directed graphs, returns outgoing neighbors.
        For undirected graphs, returns all neighbors.

        Args:
            vertex_id: Vertex ID

        Returns:
            Set of neighboring vertex IDs

        Example:
            >>> g = Graph(edges={Edge('A', 'B'), Edge('A', 'C')})
            >>> g.neighbors('A')
            {'B', 'C'}
        """
        neighbors = set()
        for e in self.edges:
            if e.source == vertex_id:
                neighbors.add(e.target)
            elif not e.directed and e.target == vertex_id:
                neighbors.add(e.source)
        return neighbors

    def degree(self, vertex_id: str) -> int:
        """
        Get degree of vertex (number of connected edges).

        Args:
            vertex_id: Vertex ID

        Returns:
            Degree of vertex

        Example:
            >>> g = Graph(edges={Edge('A', 'B'), Edge('A', 'C')})
            >>> g.degree('A')
            2
        """
        return len(self.neighbors(vertex_id))

    def in_degree(self, vertex_id: str) -> int:
        """
        Get in-degree (number of incoming edges).

        Only meaningful for directed graphs.

        Args:
            vertex_id: Vertex ID

        Returns:
            In-degree of vertex
        """
        count = 0
        for e in self.edges:
            if e.target == vertex_id:
                if e.directed:
                    count += 1
                else:
                    count += 0.5  # Undirected edge counts as 0.5 in/0.5 out
        return int(count)

    def out_degree(self, vertex_id: str) -> int:
        """
        Get out-degree (number of outgoing edges).

        Args:
            vertex_id: Vertex ID

        Returns:
            Out-degree of vertex
        """
        count = 0
        for e in self.edges:
            if e.source == vertex_id:
                if e.directed:
                    count += 1
                else:
                    count += 0.5
        return int(count)

    # ========================================================================
    # Graph Construction (Immutable Operations)
    # ========================================================================

    def add_vertex(self, vertex: Vertex) -> 'Graph':
        """
        Create new graph with added vertex.

        Args:
            vertex: Vertex to add

        Returns:
            New Graph with added vertex

        Example:
            >>> g1 = Graph()
            >>> g2 = g1.add_vertex(Vertex('A'))
            >>> g2.has_vertex('A')
            True
        """
        new_vertices = self.vertices | {vertex}
        return Graph(vertices=new_vertices, edges=self.edges)

    def add_edge(self, edge: Edge) -> 'Graph':
        """
        Create new graph with added edge.

        Automatically adds vertices if they don't exist.

        Args:
            edge: Edge to add

        Returns:
            New Graph with added edge

        Example:
            >>> g1 = Graph()
            >>> g2 = g1.add_edge(Edge('A', 'B'))
            >>> g2.has_edge('A', 'B')
            True
        """
        new_edges = self.edges | {edge}

        # Ensure vertices exist
        new_vertices = self.vertices.copy()
        if not self.has_vertex(edge.source):
            new_vertices.add(Vertex(edge.source))
        if not self.has_vertex(edge.target):
            new_vertices.add(Vertex(edge.target))

        return Graph(vertices=new_vertices, edges=new_edges)

    def remove_vertex(self, vertex_id: str) -> 'Graph':
        """
        Create new graph with removed vertex.

        Also removes all edges connected to the vertex.

        Args:
            vertex_id: Vertex ID to remove

        Returns:
            New Graph with removed vertex

        Example:
            >>> g1 = Graph({Vertex('A'), Vertex('B')}, {Edge('A', 'B')})
            >>> g2 = g1.remove_vertex('A')
            >>> g2.has_vertex('A')
            False
        """
        new_vertices = {v for v in self.vertices if v.id != vertex_id}
        new_edges = {e for e in self.edges
                     if e.source != vertex_id and e.target != vertex_id}
        return Graph(vertices=new_vertices, edges=new_edges)

    def remove_edge(self, source: str, target: str) -> 'Graph':
        """
        Create new graph with removed edge.

        Args:
            source: Source vertex ID
            target: Target vertex ID

        Returns:
            New Graph with removed edge
        """
        new_edges = {e for e in self.edges if not e.connects(source, target)}
        return Graph(vertices=self.vertices, edges=new_edges)

    def update_vertex(self, vertex: Vertex) -> 'Graph':
        """
        Create new graph with updated vertex.

        Replaces existing vertex with same ID.

        Args:
            vertex: Updated vertex

        Returns:
            New Graph with updated vertex
        """
        new_vertices = {v if v.id != vertex.id else vertex for v in self.vertices}
        return Graph(vertices=new_vertices, edges=self.edges)

    def update_edge(self, edge: Edge) -> 'Graph':
        """
        Create new graph with updated edge.

        Replaces existing edge between same vertices.

        Args:
            edge: Updated edge

        Returns:
            New Graph with updated edge
        """
        new_edges = {e if not e.connects(edge.source, edge.target) else edge
                     for e in self.edges}
        return Graph(vertices=self.vertices, edges=new_edges)

    # ========================================================================
    # Graph Queries
    # ========================================================================

    def find_vertices(self, predicate: Callable[[Vertex], bool]) -> Set[Vertex]:
        """
        Find vertices matching predicate.

        Args:
            predicate: Function that returns True for matching vertices

        Returns:
            Set of matching vertices

        Example:
            >>> g = Graph({Vertex('A', attrs={'val': 10}), Vertex('B', attrs={'val': 20})})
            >>> matches = g.find_vertices(lambda v: v.get('val', 0) > 15)
            >>> len(matches)
            1
        """
        return {v for v in self.vertices if predicate(v)}

    def find_edges(self, predicate: Callable[[Edge], bool]) -> Set[Edge]:
        """
        Find edges matching predicate.

        Args:
            predicate: Function that returns True for matching edges

        Returns:
            Set of matching edges

        Example:
            >>> g = Graph(edges={Edge('A', 'B', weight=5), Edge('B', 'C', weight=10)})
            >>> heavy = g.find_edges(lambda e: e.weight > 7)
            >>> len(heavy)
            1
        """
        return {e for e in self.edges if predicate(e)}

    def select_vertices(self, selector: 'VertexSelector') -> Set[Vertex]:
        """
        Select vertices using a Selector.

        Enables declarative vertex selection with composable selectors.

        Args:
            selector: VertexSelector instance

        Returns:
            Set of matching vertices

        Example:
            >>> from AlgoGraph.selectors import vertex as v
            >>> g = Graph({Vertex('A', attrs={'age': 30}), Vertex('B', attrs={'age': 25})})
            >>> matches = g.select_vertices(v.attrs(age=lambda a: a > 27))
            >>> len(matches)
            1
        """
        from AlgoGraph.graph_selectors import VertexSelector
        if not isinstance(selector, VertexSelector):
            raise TypeError("selector must be a VertexSelector instance")
        return set(selector.select(self))

    def select_edges(self, selector: 'EdgeSelector') -> Set[Edge]:
        """
        Select edges using a Selector.

        Enables declarative edge selection with composable selectors.

        Args:
            selector: EdgeSelector instance

        Returns:
            Set of matching edges

        Example:
            >>> from AlgoGraph.graph_selectors import edge as e
            >>> g = Graph(edges={Edge('A', 'B', weight=5), Edge('B', 'C', weight=10)})
            >>> heavy = g.select_edges(e.weight(min_weight=7))
            >>> len(heavy)
            1
        """
        from AlgoGraph.graph_selectors import EdgeSelector
        if not isinstance(selector, EdgeSelector):
            raise TypeError("selector must be an EdgeSelector instance")
        return set(selector.select(self))

    def subgraph(self, vertex_ids: Set[str]) -> 'Graph':
        """
        Extract subgraph containing only specified vertices.

        Args:
            vertex_ids: Set of vertex IDs to include

        Returns:
            New Graph containing only specified vertices and edges between them

        Example:
            >>> g1 = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
            ...            {Edge('A', 'B'), Edge('B', 'C')})
            >>> g2 = g1.subgraph({'A', 'B'})
            >>> g2.vertex_count
            2
        """
        new_vertices = {v for v in self.vertices if v.id in vertex_ids}
        new_edges = {e for e in self.edges
                     if e.source in vertex_ids and e.target in vertex_ids}
        return Graph(vertices=new_vertices, edges=new_edges)

    def __repr__(self) -> str:
        """String representation."""
        return f"Graph(vertices={self.vertex_count}, edges={self.edge_count})"

    def __str__(self) -> str:
        """Human-readable string."""
        return f"Graph with {self.vertex_count} vertices and {self.edge_count} edges"

    def __len__(self) -> int:
        """Length is number of vertices."""
        return self.vertex_count

    def __contains__(self, item) -> bool:
        """Check if vertex ID or vertex is in graph."""
        if isinstance(item, str):
            return self.has_vertex(item)
        elif isinstance(item, Vertex):
            return item in self.vertices
        return False
