"""
Query DSL for AlgoGraph.

Provides a fluent, chainable API for building complex graph queries.
Combines selectors, transformers, and path matching in a unified interface.

Example usage:
    >>> from AlgoGraph.query import Query
    >>>
    >>> # Find all active users with high degree
    >>> result = (Query(graph)
    ...     .vertices()
    ...     .where(lambda v: v.get('active'))
    ...     .where(lambda v: graph.degree(v.id) > 5)
    ...     .select())
    >>>
    >>> # Path matching
    >>> paths = (Query(graph)
    ...     .paths()
    ...     .from_vertex('A')
    ...     .to_vertex('B')
    ...     .max_length(5)
    ...     .find_all())
    >>>
    >>> # Aggregate statistics
    >>> stats = (Query(graph)
    ...     .vertices()
    ...     .where(lambda v: v.get('region') == 'US')
    ...     .aggregate()
    ...     .count()
    ...     .avg('score')
    ...     .result())
"""

from typing import (
    Any, Callable, Dict, Generic, Iterator, List, Optional,
    Set, Tuple, TypeVar, Union
)
from dataclasses import dataclass, field
from collections import deque

from .graph import Graph
from .vertex import Vertex
from .edge import Edge


T = TypeVar('T')


@dataclass
class QueryResult(Generic[T]):
    """
    Container for query results with metadata.

    Provides iteration, conversion, and utility methods.
    """
    items: List[T]
    source_graph: Graph
    query_type: str = "vertices"

    def __iter__(self) -> Iterator[T]:
        """Iterate over results."""
        return iter(self.items)

    def __len__(self) -> int:
        """Number of results."""
        return len(self.items)

    def __bool__(self) -> bool:
        """True if any results."""
        return len(self.items) > 0

    def first(self) -> Optional[T]:
        """Get first result or None."""
        return self.items[0] if self.items else None

    def to_list(self) -> List[T]:
        """Convert to list."""
        return list(self.items)

    def to_set(self) -> Set[T]:
        """Convert to set."""
        return set(self.items)

    def ids(self) -> List[str]:
        """Get IDs (for vertex results)."""
        if self.query_type == "vertices":
            return [v.id for v in self.items]
        elif self.query_type == "edges":
            return [f"{e.source}->{e.target}" for e in self.items]
        return []

    def to_subgraph(self) -> Graph:
        """Convert vertex results to a subgraph."""
        if self.query_type != "vertices":
            raise ValueError("to_subgraph() only works with vertex queries")

        vertex_ids = {v.id for v in self.items}
        vertices = set(self.items)
        edges = {
            e for e in self.source_graph.edges
            if e.source in vertex_ids and e.target in vertex_ids
        }
        return Graph(vertices=vertices, edges=edges)


@dataclass
class AggregateBuilder:
    """Builder for aggregate operations on query results."""

    items: List[Any]
    _results: Dict[str, Any] = field(default_factory=dict)

    def count(self) -> 'AggregateBuilder':
        """Count items."""
        self._results['count'] = len(self.items)
        return self

    def sum(self, attr: str) -> 'AggregateBuilder':
        """Sum an attribute."""
        values = [item.get(attr, 0) for item in self.items if hasattr(item, 'get')]
        self._results[f'sum_{attr}'] = sum(v for v in values if v is not None)
        return self

    def avg(self, attr: str) -> 'AggregateBuilder':
        """Average an attribute."""
        values = [item.get(attr) for item in self.items if hasattr(item, 'get')]
        values = [v for v in values if v is not None]
        if values:
            self._results[f'avg_{attr}'] = sum(values) / len(values)
        else:
            self._results[f'avg_{attr}'] = None
        return self

    def min(self, attr: str) -> 'AggregateBuilder':
        """Minimum of an attribute."""
        values = [item.get(attr) for item in self.items if hasattr(item, 'get')]
        values = [v for v in values if v is not None]
        self._results[f'min_{attr}'] = min(values) if values else None
        return self

    def max(self, attr: str) -> 'AggregateBuilder':
        """Maximum of an attribute."""
        values = [item.get(attr) for item in self.items if hasattr(item, 'get')]
        values = [v for v in values if v is not None]
        self._results[f'max_{attr}'] = max(values) if values else None
        return self

    def group_by(self, attr: str) -> Dict[Any, List[Any]]:
        """Group items by attribute."""
        groups: Dict[Any, List[Any]] = {}
        for item in self.items:
            if hasattr(item, 'get'):
                key = item.get(attr)
                if key not in groups:
                    groups[key] = []
                groups[key].append(item)
        return groups

    def result(self) -> Dict[str, Any]:
        """Get aggregate results."""
        return self._results


class VertexQuery:
    """Builder for vertex queries."""

    def __init__(self, graph: Graph, vertices: Optional[Set[Vertex]] = None):
        self.graph = graph
        self._vertices = vertices if vertices is not None else graph.vertices
        self._predicates: List[Callable[[Vertex], bool]] = []
        self._limit: Optional[int] = None
        self._offset: int = 0
        self._sort_key: Optional[Callable[[Vertex], Any]] = None
        self._sort_reverse: bool = False

    def where(self, predicate: Callable[[Vertex], bool]) -> 'VertexQuery':
        """Add a filter predicate."""
        self._predicates.append(predicate)
        return self

    def has(self, attr: str, value: Any = None) -> 'VertexQuery':
        """Filter vertices with attribute (optionally matching value)."""
        if value is None:
            self._predicates.append(lambda v: attr in v.attrs)
        else:
            self._predicates.append(lambda v, a=attr, val=value: v.get(a) == val)
        return self

    def has_not(self, attr: str) -> 'VertexQuery':
        """Filter vertices without attribute."""
        self._predicates.append(lambda v, a=attr: a not in v.attrs)
        return self

    def degree_at_least(self, min_degree: int) -> 'VertexQuery':
        """Filter by minimum degree."""
        self._predicates.append(
            lambda v, g=self.graph, d=min_degree: g.degree(v.id) >= d
        )
        return self

    def degree_at_most(self, max_degree: int) -> 'VertexQuery':
        """Filter by maximum degree."""
        self._predicates.append(
            lambda v, g=self.graph, d=max_degree: g.degree(v.id) <= d
        )
        return self

    def neighbors_of(self, vertex_id: str) -> 'VertexQuery':
        """Filter to neighbors of a vertex."""
        neighbor_ids = set(self.graph.neighbors(vertex_id))
        self._vertices = {v for v in self._vertices if v.id in neighbor_ids}
        return self

    def reachable_from(self, vertex_id: str, max_depth: Optional[int] = None) -> 'VertexQuery':
        """Filter to vertices reachable from a vertex."""
        reachable = self._bfs_reachable(vertex_id, max_depth)
        self._vertices = {v for v in self._vertices if v.id in reachable}
        return self

    def _bfs_reachable(self, start: str, max_depth: Optional[int]) -> Set[str]:
        """BFS to find reachable vertices."""
        visited = {start}
        queue = deque([(start, 0)])

        while queue:
            current, depth = queue.popleft()
            if max_depth is not None and depth >= max_depth:
                continue

            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        return visited

    def order_by(self, key: Callable[[Vertex], Any],
                 reverse: bool = False) -> 'VertexQuery':
        """Sort results by key."""
        self._sort_key = key
        self._sort_reverse = reverse
        return self

    def limit(self, n: int) -> 'VertexQuery':
        """Limit number of results."""
        self._limit = n
        return self

    def offset(self, n: int) -> 'VertexQuery':
        """Skip first n results."""
        self._offset = n
        return self

    def select(self) -> QueryResult[Vertex]:
        """Execute query and return results."""
        # Apply predicates
        result = self._vertices
        for pred in self._predicates:
            result = {v for v in result if pred(v)}

        # Convert to list for sorting/slicing
        result_list = list(result)

        # Sort if specified
        if self._sort_key is not None:
            result_list.sort(key=self._sort_key, reverse=self._sort_reverse)

        # Apply offset and limit
        if self._offset:
            result_list = result_list[self._offset:]
        if self._limit is not None:
            result_list = result_list[:self._limit]

        return QueryResult(
            items=result_list,
            source_graph=self.graph,
            query_type="vertices"
        )

    def count(self) -> int:
        """Count matching vertices."""
        return len(self.select())

    def exists(self) -> bool:
        """Check if any vertices match."""
        return len(self.select()) > 0

    def aggregate(self) -> AggregateBuilder:
        """Start aggregate operations."""
        return AggregateBuilder(items=self.select().to_list())


class EdgeQuery:
    """Builder for edge queries."""

    def __init__(self, graph: Graph, edges: Optional[Set[Edge]] = None):
        self.graph = graph
        self._edges = edges if edges is not None else graph.edges
        self._predicates: List[Callable[[Edge], bool]] = []
        self._limit: Optional[int] = None
        self._offset: int = 0
        self._sort_key: Optional[Callable[[Edge], Any]] = None
        self._sort_reverse: bool = False

    def where(self, predicate: Callable[[Edge], bool]) -> 'EdgeQuery':
        """Add a filter predicate."""
        self._predicates.append(predicate)
        return self

    def from_vertex(self, vertex_id: str) -> 'EdgeQuery':
        """Filter edges from a specific vertex."""
        self._predicates.append(lambda e, v=vertex_id: e.source == v)
        return self

    def to_vertex(self, vertex_id: str) -> 'EdgeQuery':
        """Filter edges to a specific vertex."""
        self._predicates.append(lambda e, v=vertex_id: e.target == v)
        return self

    def between(self, vertex_id1: str, vertex_id2: str) -> 'EdgeQuery':
        """Filter edges between two vertices (either direction)."""
        self._predicates.append(
            lambda e, v1=vertex_id1, v2=vertex_id2:
            (e.source == v1 and e.target == v2) or
            (e.source == v2 and e.target == v1)
        )
        return self

    def weight_at_least(self, min_weight: float) -> 'EdgeQuery':
        """Filter by minimum weight."""
        self._predicates.append(lambda e, w=min_weight: e.weight >= w)
        return self

    def weight_at_most(self, max_weight: float) -> 'EdgeQuery':
        """Filter by maximum weight."""
        self._predicates.append(lambda e, w=max_weight: e.weight <= w)
        return self

    def weight_between(self, min_weight: float, max_weight: float) -> 'EdgeQuery':
        """Filter by weight range."""
        self._predicates.append(
            lambda e, lo=min_weight, hi=max_weight: lo <= e.weight <= hi
        )
        return self

    def has(self, attr: str, value: Any = None) -> 'EdgeQuery':
        """Filter edges with attribute."""
        if value is None:
            self._predicates.append(lambda e, a=attr: a in e.attrs)
        else:
            self._predicates.append(lambda e, a=attr, val=value: e.attrs.get(a) == val)
        return self

    def order_by(self, key: Callable[[Edge], Any],
                 reverse: bool = False) -> 'EdgeQuery':
        """Sort results by key."""
        self._sort_key = key
        self._sort_reverse = reverse
        return self

    def order_by_weight(self, reverse: bool = False) -> 'EdgeQuery':
        """Sort by edge weight."""
        return self.order_by(lambda e: e.weight, reverse=reverse)

    def limit(self, n: int) -> 'EdgeQuery':
        """Limit number of results."""
        self._limit = n
        return self

    def offset(self, n: int) -> 'EdgeQuery':
        """Skip first n results."""
        self._offset = n
        return self

    def select(self) -> QueryResult[Edge]:
        """Execute query and return results."""
        result = self._edges
        for pred in self._predicates:
            result = {e for e in result if pred(e)}

        result_list = list(result)

        if self._sort_key is not None:
            result_list.sort(key=self._sort_key, reverse=self._sort_reverse)

        if self._offset:
            result_list = result_list[self._offset:]
        if self._limit is not None:
            result_list = result_list[:self._limit]

        return QueryResult(
            items=result_list,
            source_graph=self.graph,
            query_type="edges"
        )

    def count(self) -> int:
        """Count matching edges."""
        return len(self.select())

    def exists(self) -> bool:
        """Check if any edges match."""
        return len(self.select()) > 0

    def total_weight(self) -> float:
        """Sum of edge weights."""
        return sum(e.weight for e in self.select())


@dataclass
class Path:
    """Represents a path through the graph."""
    vertices: List[str]
    edges: List[Edge]

    @property
    def length(self) -> int:
        """Number of edges in path."""
        return len(self.edges)

    @property
    def total_weight(self) -> float:
        """Sum of edge weights."""
        return sum(e.weight for e in self.edges)

    @property
    def start(self) -> str:
        """Starting vertex."""
        return self.vertices[0] if self.vertices else ""

    @property
    def end(self) -> str:
        """Ending vertex."""
        return self.vertices[-1] if self.vertices else ""

    def __repr__(self) -> str:
        return f"Path({' -> '.join(self.vertices)})"


class PathQuery:
    """Builder for path queries."""

    def __init__(self, graph: Graph):
        self.graph = graph
        self._start: Optional[str] = None
        self._end: Optional[str] = None
        self._max_length: Optional[int] = None
        self._min_length: int = 0
        self._avoid_vertices: Set[str] = set()
        self._require_vertices: Set[str] = set()

    def from_vertex(self, vertex_id: str) -> 'PathQuery':
        """Set starting vertex."""
        self._start = vertex_id
        return self

    def to_vertex(self, vertex_id: str) -> 'PathQuery':
        """Set ending vertex."""
        self._end = vertex_id
        return self

    def max_length(self, length: int) -> 'PathQuery':
        """Set maximum path length."""
        self._max_length = length
        return self

    def min_length(self, length: int) -> 'PathQuery':
        """Set minimum path length."""
        self._min_length = length
        return self

    def avoiding(self, *vertex_ids: str) -> 'PathQuery':
        """Avoid specific vertices."""
        self._avoid_vertices.update(vertex_ids)
        return self

    def through(self, *vertex_ids: str) -> 'PathQuery':
        """Require path to pass through vertices."""
        self._require_vertices.update(vertex_ids)
        return self

    def find_shortest(self) -> Optional[Path]:
        """Find shortest path."""
        if self._start is None or self._end is None:
            raise ValueError("Must specify start and end vertices")

        paths = list(self._find_all_bfs(limit=1))
        return paths[0] if paths else None

    def find_all(self, limit: Optional[int] = None) -> List[Path]:
        """Find all paths matching criteria."""
        if self._start is None or self._end is None:
            raise ValueError("Must specify start and end vertices")

        return list(self._find_all_dfs(limit=limit))

    def exists(self) -> bool:
        """Check if any path exists."""
        return self.find_shortest() is not None

    def _find_all_bfs(self, limit: Optional[int] = None) -> Iterator[Path]:
        """BFS to find paths (yields shortest first)."""
        if self._start == self._end and self._min_length == 0:
            yield Path(vertices=[self._start], edges=[])
            return

        # BFS with path tracking
        queue = deque([(self._start, [self._start], [])])
        count = 0

        while queue:
            current, path_vertices, path_edges = queue.popleft()

            if limit is not None and count >= limit:
                break

            for edge in self.graph.edges:
                if edge.source != current:
                    continue

                neighbor = edge.target

                # Skip if avoiding
                if neighbor in self._avoid_vertices:
                    continue

                # Skip if already in path (no cycles)
                if neighbor in path_vertices:
                    continue

                new_vertices = path_vertices + [neighbor]
                new_edges = path_edges + [edge]
                path_length = len(new_edges)

                # Check max length
                if self._max_length is not None and path_length > self._max_length:
                    continue

                if neighbor == self._end:
                    # Found path to destination
                    if path_length >= self._min_length:
                        # Check required vertices
                        if self._require_vertices.issubset(set(new_vertices)):
                            yield Path(vertices=new_vertices, edges=new_edges)
                            count += 1
                            if limit is not None and count >= limit:
                                return
                else:
                    # Continue searching
                    queue.append((neighbor, new_vertices, new_edges))

    def _find_all_dfs(self, limit: Optional[int] = None) -> Iterator[Path]:
        """DFS to find all paths."""
        if self._start == self._end and self._min_length == 0:
            yield Path(vertices=[self._start], edges=[])
            return

        count = 0
        stack = [(self._start, [self._start], [])]

        while stack:
            current, path_vertices, path_edges = stack.pop()

            if limit is not None and count >= limit:
                break

            for edge in self.graph.edges:
                if edge.source != current:
                    continue

                neighbor = edge.target

                if neighbor in self._avoid_vertices:
                    continue

                if neighbor in path_vertices:
                    continue

                new_vertices = path_vertices + [neighbor]
                new_edges = path_edges + [edge]
                path_length = len(new_edges)

                if self._max_length is not None and path_length > self._max_length:
                    continue

                if neighbor == self._end:
                    if path_length >= self._min_length:
                        if self._require_vertices.issubset(set(new_vertices)):
                            yield Path(vertices=new_vertices, edges=new_edges)
                            count += 1
                            if limit is not None and count >= limit:
                                return
                else:
                    stack.append((neighbor, new_vertices, new_edges))


class Query:
    """
    Main query builder for graph operations.

    Provides a fluent interface for querying graphs.

    Example:
        >>> result = (Query(graph)
        ...     .vertices()
        ...     .where(lambda v: v.get('active'))
        ...     .order_by(lambda v: v.get('score'), reverse=True)
        ...     .limit(10)
        ...     .select())
    """

    def __init__(self, graph: Graph):
        """
        Create a query builder for a graph.

        Args:
            graph: The graph to query
        """
        self.graph = graph

    def vertices(self) -> VertexQuery:
        """Start a vertex query."""
        return VertexQuery(self.graph)

    def edges(self) -> EdgeQuery:
        """Start an edge query."""
        return EdgeQuery(self.graph)

    def paths(self) -> PathQuery:
        """Start a path query."""
        return PathQuery(self.graph)

    def vertex(self, vertex_id: str) -> Optional[Vertex]:
        """Get a specific vertex by ID."""
        return self.graph.get_vertex(vertex_id)

    def edge(self, source: str, target: str) -> Optional[Edge]:
        """Get a specific edge by endpoints."""
        return self.graph.get_edge(source, target)

    def subgraph(self, vertex_ids: Set[str]) -> Graph:
        """Extract a subgraph containing only specified vertices."""
        vertices = {v for v in self.graph.vertices if v.id in vertex_ids}
        edges = {
            e for e in self.graph.edges
            if e.source in vertex_ids and e.target in vertex_ids
        }
        return Graph(vertices=vertices, edges=edges)

    def neighbors(self, vertex_id: str, depth: int = 1) -> QueryResult[Vertex]:
        """Get neighbors within a certain depth."""
        return (self.vertices()
                .reachable_from(vertex_id, max_depth=depth)
                .where(lambda v, vid=vertex_id: v.id != vid)
                .select())


# Convenience function
def query(graph: Graph) -> Query:
    """
    Create a query builder for a graph.

    Args:
        graph: The graph to query

    Returns:
        Query builder instance

    Example:
        >>> from AlgoGraph.query import query
        >>> result = query(g).vertices().where(lambda v: v.get('active')).select()
    """
    return Query(graph)
