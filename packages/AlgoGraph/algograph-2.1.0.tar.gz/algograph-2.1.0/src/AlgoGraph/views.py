"""
Lazy graph views for efficient filtering and querying.

This module provides view classes that enable lazy evaluation of graph
operations without copying data. Views are particularly useful for large
graphs where creating subgraphs would be expensive.

Inspired by Python's dict_keys/dict_values views and database query views.
"""

from typing import Iterator, Set, Callable, Optional
from abc import ABC, abstractmethod

from AlgoGraph.graph import Graph
from AlgoGraph.vertex import Vertex
from AlgoGraph.edge import Edge


class GraphView(ABC):
    """
    Abstract base class for lazy graph views.

    Views provide a read-only window into a graph with optional filtering.
    They don't copy data until explicitly materialized.
    """

    def __init__(self, graph: Graph):
        """
        Create view of graph.

        Args:
            graph: Source graph to view
        """
        self._graph = graph

    @property
    def graph(self) -> Graph:
        """Get underlying graph."""
        return self._graph

    @abstractmethod
    def vertices(self) -> Iterator[Vertex]:
        """
        Iterate over vertices in view.

        Returns:
            Iterator of vertices
        """
        pass

    @abstractmethod
    def edges(self) -> Iterator[Edge]:
        """
        Iterate over edges in view.

        Returns:
            Iterator of edges
        """
        pass

    @property
    def vertex_count(self) -> int:
        """
        Count vertices in view.

        Returns:
            Number of vertices
        """
        return sum(1 for _ in self.vertices())

    @property
    def edge_count(self) -> int:
        """
        Count edges in view.

        Returns:
            Number of edges
        """
        return sum(1 for _ in self.edges())

    def materialize(self) -> Graph:
        """
        Materialize view into a concrete Graph.

        Creates a new Graph containing all vertices and edges from the view.

        Returns:
            New Graph instance

        Example:
            >>> view = FilteredView(large_graph, vertex_filter=lambda v: v.get('active'))
            >>> small_graph = view.materialize()  # Copy only active subgraph
        """
        return Graph(
            vertices=set(self.vertices()),
            edges=set(self.edges())
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(vertices={self.vertex_count}, edges={self.edge_count})"


class FilteredView(GraphView):
    """
    Filtered view of a graph.

    Lazily filters vertices and edges without copying.
    """

    def __init__(
        self,
        graph: Graph,
        vertex_filter: Optional[Callable[[Vertex], bool]] = None,
        edge_filter: Optional[Callable[[Edge], bool]] = None
    ):
        """
        Create filtered view.

        Args:
            graph: Source graph
            vertex_filter: Optional predicate for vertices
            edge_filter: Optional predicate for edges

        Example:
            >>> view = FilteredView(
            ...     graph,
            ...     vertex_filter=lambda v: v.get('active'),
            ...     edge_filter=lambda e: e.weight > 5.0
            ... )
        """
        super().__init__(graph)
        self._vertex_filter = vertex_filter
        self._edge_filter = edge_filter

        # Cache vertex IDs for edge filtering
        self._vertex_ids: Optional[Set[str]] = None

    def vertices(self) -> Iterator[Vertex]:
        """Iterate over filtered vertices."""
        if self._vertex_filter is None:
            yield from self._graph.vertices
        else:
            for v in self._graph.vertices:
                if self._vertex_filter(v):
                    yield v

    def edges(self) -> Iterator[Edge]:
        """Iterate over filtered edges."""
        # Lazy compute vertex IDs if we have a vertex filter
        if self._vertex_filter is not None:
            if self._vertex_ids is None:
                self._vertex_ids = {v.id for v in self.vertices()}

            # Filter edges to only those between included vertices
            for e in self._graph.edges:
                if e.source in self._vertex_ids and e.target in self._vertex_ids:
                    if self._edge_filter is None or self._edge_filter(e):
                        yield e
        else:
            # No vertex filter, just apply edge filter
            if self._edge_filter is None:
                yield from self._graph.edges
            else:
                for e in self._graph.edges:
                    if self._edge_filter(e):
                        yield e

    def __repr__(self) -> str:
        filters = []
        if self._vertex_filter:
            filters.append("vertex_filter")
        if self._edge_filter:
            filters.append("edge_filter")
        filter_str = ", ".join(filters) if filters else "no filters"
        return f"FilteredView({filter_str})"


class SubGraphView(GraphView):
    """
    View of a subgraph defined by vertex IDs.

    Efficiently represents a subgraph without copying.
    """

    def __init__(self, graph: Graph, vertex_ids: Set[str]):
        """
        Create subgraph view.

        Args:
            graph: Source graph
            vertex_ids: Set of vertex IDs to include

        Example:
            >>> view = SubGraphView(graph, {'A', 'B', 'C'})
        """
        super().__init__(graph)
        self._vertex_ids = vertex_ids

    def vertices(self) -> Iterator[Vertex]:
        """Iterate over vertices in subgraph."""
        for v in self._graph.vertices:
            if v.id in self._vertex_ids:
                yield v

    def edges(self) -> Iterator[Edge]:
        """Iterate over edges in subgraph."""
        for e in self._graph.edges:
            if e.source in self._vertex_ids and e.target in self._vertex_ids:
                yield e

    def __repr__(self) -> str:
        return f"SubGraphView({len(self._vertex_ids)} vertices)"


class ReversedView(GraphView):
    """
    View of graph with all edges reversed.

    Lazily reverses directed edges without copying.
    """

    def vertices(self) -> Iterator[Vertex]:
        """Iterate over vertices (unchanged)."""
        yield from self._graph.vertices

    def edges(self) -> Iterator[Edge]:
        """Iterate over reversed edges."""
        for e in self._graph.edges:
            if e.directed:
                yield e.reversed()
            else:
                yield e

    def __repr__(self) -> str:
        return "ReversedView()"


class UndirectedView(GraphView):
    """
    View of graph with all edges made undirected.

    Lazily converts edges without copying.
    """

    def vertices(self) -> Iterator[Vertex]:
        """Iterate over vertices (unchanged)."""
        yield from self._graph.vertices

    def edges(self) -> Iterator[Edge]:
        """Iterate over undirected edges."""
        for e in self._graph.edges:
            if e.directed:
                yield Edge(e.source, e.target, directed=False, weight=e.weight, attrs=e.attrs)
            else:
                yield e

    def __repr__(self) -> str:
        return "UndirectedView()"


class ComponentView(GraphView):
    """
    View of a single connected component.

    Efficiently represents a component without copying.
    """

    def __init__(self, graph: Graph, component_vertices: Set[str]):
        """
        Create component view.

        Args:
            graph: Source graph
            component_vertices: Vertex IDs in the component

        Example:
            >>> from AlgoGraph.algorithms import connected_components
            >>> components = connected_components(graph)
            >>> view = ComponentView(graph, components[0])
        """
        super().__init__(graph)
        self._component_vertices = component_vertices

    def vertices(self) -> Iterator[Vertex]:
        """Iterate over vertices in component."""
        for v in self._graph.vertices:
            if v.id in self._component_vertices:
                yield v

    def edges(self) -> Iterator[Edge]:
        """Iterate over edges in component."""
        for e in self._graph.edges:
            if e.source in self._component_vertices and e.target in self._component_vertices:
                yield e

    def __repr__(self) -> str:
        return f"ComponentView({len(self._component_vertices)} vertices)"


class NeighborhoodView(GraphView):
    """
    View of k-hop neighborhood around a vertex.

    Includes vertex and all vertices within k hops.
    """

    def __init__(self, graph: Graph, center: str, k: int = 1):
        """
        Create neighborhood view.

        Args:
            graph: Source graph
            center: Central vertex ID
            k: Number of hops (default: 1)

        Example:
            >>> view = NeighborhoodView(graph, 'A', k=2)  # 2-hop neighborhood
        """
        super().__init__(graph)
        self._center = center
        self._k = k
        self._neighborhood: Optional[Set[str]] = None

    def _compute_neighborhood(self) -> Set[str]:
        """Compute k-hop neighborhood."""
        from collections import deque

        neighborhood = {self._center}
        current_level = {self._center}

        for _ in range(self._k):
            next_level = set()
            for vertex_id in current_level:
                for neighbor_id in self._graph.neighbors(vertex_id):
                    if neighbor_id not in neighborhood:
                        next_level.add(neighbor_id)
                        neighborhood.add(neighbor_id)
            current_level = next_level

            if not current_level:
                break

        return neighborhood

    def vertices(self) -> Iterator[Vertex]:
        """Iterate over vertices in neighborhood."""
        if self._neighborhood is None:
            self._neighborhood = self._compute_neighborhood()

        for v in self._graph.vertices:
            if v.id in self._neighborhood:
                yield v

    def edges(self) -> Iterator[Edge]:
        """Iterate over edges in neighborhood."""
        if self._neighborhood is None:
            self._neighborhood = self._compute_neighborhood()

        for e in self._graph.edges:
            if e.source in self._neighborhood and e.target in self._neighborhood:
                yield e

    def __repr__(self) -> str:
        return f"NeighborhoodView(center={self._center!r}, k={self._k})"


# Convenience functions for creating views

def filtered_view(
    graph: Graph,
    vertex_filter: Optional[Callable[[Vertex], bool]] = None,
    edge_filter: Optional[Callable[[Edge], bool]] = None
) -> FilteredView:
    """
    Create filtered view of graph.

    Args:
        graph: Source graph
        vertex_filter: Optional predicate for vertices
        edge_filter: Optional predicate for edges

    Returns:
        FilteredView instance

    Example:
        >>> view = filtered_view(graph, vertex_filter=lambda v: v.get('active'))
    """
    return FilteredView(graph, vertex_filter, edge_filter)


def subgraph_view(graph: Graph, vertex_ids: Set[str]) -> SubGraphView:
    """
    Create subgraph view.

    Args:
        graph: Source graph
        vertex_ids: Vertex IDs to include

    Returns:
        SubGraphView instance

    Example:
        >>> view = subgraph_view(graph, {'A', 'B', 'C'})
    """
    return SubGraphView(graph, vertex_ids)


def reversed_view(graph: Graph) -> ReversedView:
    """
    Create reversed view.

    Args:
        graph: Source graph

    Returns:
        ReversedView instance

    Example:
        >>> view = reversed_view(directed_graph)
    """
    return ReversedView(graph)


def undirected_view(graph: Graph) -> UndirectedView:
    """
    Create undirected view.

    Args:
        graph: Source graph

    Returns:
        UndirectedView instance

    Example:
        >>> view = undirected_view(directed_graph)
    """
    return UndirectedView(graph)


def component_view(graph: Graph, component_vertices: Set[str]) -> ComponentView:
    """
    Create component view.

    Args:
        graph: Source graph
        component_vertices: Vertex IDs in component

    Returns:
        ComponentView instance

    Example:
        >>> from AlgoGraph.algorithms import connected_components
        >>> components = connected_components(graph)
        >>> view = component_view(graph, components[0])
    """
    return ComponentView(graph, component_vertices)


def neighborhood_view(graph: Graph, center: str, k: int = 1) -> NeighborhoodView:
    """
    Create k-hop neighborhood view.

    Args:
        graph: Source graph
        center: Central vertex ID
        k: Number of hops

    Returns:
        NeighborhoodView instance

    Example:
        >>> view = neighborhood_view(graph, 'A', k=2)
    """
    return NeighborhoodView(graph, center, k)
