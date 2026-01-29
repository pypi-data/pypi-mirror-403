"""
Spanning tree algorithms.

Provides algorithms for finding minimum spanning trees:
- Kruskal's algorithm
- Prim's algorithm
"""

from typing import Set, Optional
import heapq

from AlgoGraph.graph import Graph
from AlgoGraph.edge import Edge
from AlgoGraph.vertex import Vertex


class UnionFind:
    """
    Union-Find (Disjoint Set Union) data structure.

    Used for cycle detection in Kruskal's algorithm.
    """

    def __init__(self, vertices: Set[str]):
        """Initialize with vertices."""
        self.parent = {v: v for v in vertices}
        self.rank = {v: 0 for v in vertices}

    def find(self, x: str) -> str:
        """Find root of set containing x (with path compression)."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str) -> bool:
        """
        Union sets containing x and y (with union by rank).

        Returns:
            True if union was performed, False if already in same set
        """
        root_x = self.find(x)
        root_y = self.find(y)

        if root_x == root_y:
            return False

        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

        return True


def kruskal(graph: Graph) -> Graph:
    """
    Find minimum spanning tree using Kruskal's algorithm.

    Greedy algorithm that adds edges in order of increasing weight,
    skipping edges that would create a cycle.

    Args:
        graph: Undirected graph

    Returns:
        Minimum spanning tree as a new Graph

    Raises:
        ValueError: If graph is directed or not connected

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', weight=1, directed=False),
        ...            Edge('B', 'C', weight=2, directed=False),
        ...            Edge('A', 'C', weight=3, directed=False)})
        >>> mst = kruskal(g)
        >>> mst.edge_count
        2
    """
    if graph.is_directed:
        raise ValueError("Kruskal's algorithm requires an undirected graph")

    # Sort edges by weight
    sorted_edges = sorted(graph.edges, key=lambda e: e.weight)

    # Initialize Union-Find
    vertex_ids = {v.id for v in graph.vertices}
    uf = UnionFind(vertex_ids)

    # Build MST
    mst_edges = set()

    for edge in sorted_edges:
        # Check if adding this edge creates a cycle
        if uf.union(edge.source, edge.target):
            mst_edges.add(edge)

            # Stop when we have |V| - 1 edges
            if len(mst_edges) == graph.vertex_count - 1:
                break

    return Graph(vertices=graph.vertices, edges=mst_edges)


def prim(graph: Graph, start: Optional[str] = None) -> Graph:
    """
    Find minimum spanning tree using Prim's algorithm.

    Greedy algorithm that grows MST one vertex at a time,
    always adding the minimum-weight edge connecting the tree to a new vertex.

    Args:
        graph: Undirected graph
        start: Starting vertex ID (optional, uses first vertex if not specified)

    Returns:
        Minimum spanning tree as a new Graph

    Raises:
        ValueError: If graph is directed or not connected

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', weight=1, directed=False),
        ...            Edge('B', 'C', weight=2, directed=False),
        ...            Edge('A', 'C', weight=3, directed=False)})
        >>> mst = prim(g)
        >>> mst.edge_count
        2
    """
    if graph.is_directed:
        raise ValueError("Prim's algorithm requires an undirected graph")

    if graph.vertex_count == 0:
        return Graph()

    # Choose starting vertex
    if start is None:
        start = next(iter(graph.vertices)).id

    # Initialize
    visited = {start}
    mst_edges = set()

    # Priority queue of edges: (weight, source, target)
    pq = []

    # Helper to find edge between two vertices (handles undirected)
    def find_edge(u: str, v: str):
        for edge in graph.edges:
            if edge.connects(u, v):
                return edge
        return None

    # Add all edges from start vertex
    for neighbor in graph.neighbors(start):
        edge = find_edge(start, neighbor)
        if edge:
            heapq.heappush(pq, (edge.weight, start, neighbor, edge))

    # Build MST
    while pq and len(visited) < graph.vertex_count:
        weight, u, v, edge = heapq.heappop(pq)

        # Skip if both vertices already in MST
        if v in visited:
            continue

        # Add edge to MST
        mst_edges.add(edge)
        visited.add(v)

        # Add all edges from newly added vertex
        for neighbor in graph.neighbors(v):
            if neighbor not in visited:
                neighbor_edge = find_edge(v, neighbor)
                if neighbor_edge:
                    heapq.heappush(pq, (neighbor_edge.weight, v, neighbor, neighbor_edge))

    return Graph(vertices=graph.vertices, edges=mst_edges)


def minimum_spanning_tree(graph: Graph, algorithm: str = 'kruskal') -> Graph:
    """
    Find minimum spanning tree.

    Wrapper function that calls either Kruskal or Prim.

    Args:
        graph: Undirected graph
        algorithm: Algorithm to use ('kruskal' or 'prim')

    Returns:
        Minimum spanning tree

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', weight=1, directed=False),
        ...            Edge('B', 'C', weight=2, directed=False)})
        >>> mst = minimum_spanning_tree(g)
        >>> mst.edge_count
        2
    """
    if algorithm == 'kruskal':
        return kruskal(graph)
    elif algorithm == 'prim':
        return prim(graph)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}. Use 'kruskal' or 'prim'")


def total_weight(graph: Graph) -> float:
    """
    Calculate total weight of all edges in graph.

    Args:
        graph: Graph to analyze

    Returns:
        Sum of all edge weights

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B')},
        ...           {Edge('A', 'B', weight=5.0)})
        >>> total_weight(g)
        5.0
    """
    return sum(edge.weight for edge in graph.edges)


def is_spanning_tree(graph: Graph, tree: Graph) -> bool:
    """
    Check if tree is a spanning tree of graph.

    Args:
        graph: Original graph
        tree: Potential spanning tree

    Returns:
        True if tree is a spanning tree of graph

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', directed=False),
        ...            Edge('B', 'C', directed=False),
        ...            Edge('A', 'C', directed=False)})
        >>> mst = kruskal(g)
        >>> is_spanning_tree(g, mst)
        True
    """
    # Must have same vertices
    if tree.vertices != graph.vertices:
        return False

    # Must have |V| - 1 edges
    if tree.edge_count != graph.vertex_count - 1:
        return False

    # All edges in tree must be in original graph
    for edge in tree.edges:
        if not graph.has_edge(edge.source, edge.target):
            return False

    # Must be connected (this is implied by having |V| - 1 edges and being acyclic)
    from .connectivity import is_connected
    return is_connected(tree)
