"""
Graph matching algorithms.

Provides algorithms for finding matchings in graphs:
- Hopcroft-Karp: Maximum cardinality bipartite matching
- Maximum Matching: Generic maximum matching
- Perfect Matching: Check if perfect matching exists
"""

from typing import Dict, Set, Optional, Tuple, List
from collections import deque

from AlgoGraph.graph import Graph


def hopcroft_karp(
    graph: Graph,
    left: Set[str],
    right: Set[str]
) -> Dict[str, str]:
    """
    Hopcroft-Karp maximum bipartite matching algorithm.

    Finds a maximum cardinality matching in a bipartite graph.
    Runs in O(E * sqrt(V)) time.

    Args:
        graph: Bipartite graph (edges should only go between left and right)
        left: Set of vertex IDs in the left partition
        right: Set of vertex IDs in the right partition

    Returns:
        Dict mapping matched left vertices to matched right vertices

    Example:
        >>> from AlgoGraph import Graph
        >>> # Bipartite matching: jobs to workers
        >>> g = (Graph.builder()
        ...      .add_edge('Worker1', 'Job1', directed=False)
        ...      .add_edge('Worker1', 'Job2', directed=False)
        ...      .add_edge('Worker2', 'Job2', directed=False)
        ...      .build())
        >>> left = {'Worker1', 'Worker2'}
        >>> right = {'Job1', 'Job2'}
        >>> matching = hopcroft_karp(g, left, right)
        >>> len(matching)
        2

    References:
        Hopcroft, J. E., & Karp, R. M. (1973).
        An n^5/2 algorithm for maximum matchings in bipartite graphs.
    """
    # Validate partitions
    for v_id in left:
        if not graph.has_vertex(v_id):
            raise ValueError(f"Left vertex '{v_id}' not found in graph")
    for v_id in right:
        if not graph.has_vertex(v_id):
            raise ValueError(f"Right vertex '{v_id}' not found in graph")

    # Initialize matching
    pair_u = {u: None for u in left}   # Matching from left to right
    pair_v = {v: None for v in right}  # Matching from right to left
    dist = {}

    def bfs() -> bool:
        """BFS to find augmenting paths and compute distances."""
        queue = deque()

        # Start from unmatched vertices in left partition
        for u in left:
            if pair_u[u] is None:
                dist[u] = 0
                queue.append(u)
            else:
                dist[u] = float('inf')

        dist[None] = float('inf')

        while queue:
            u = queue.popleft()

            if dist[u] < dist[None]:
                # Explore neighbors in right partition
                for v in graph.neighbors(u):
                    if v in right:
                        matched_to_v = pair_v[v]
                        if dist.get(matched_to_v, float('inf')) == float('inf'):
                            dist[matched_to_v] = dist[u] + 1
                            if matched_to_v is not None:
                                queue.append(matched_to_v)

        return dist[None] != float('inf')

    def dfs(u: Optional[str]) -> bool:
        """DFS to find augmenting path from u."""
        if u is None:
            return True

        for v in graph.neighbors(u):
            if v in right:
                matched_to_v = pair_v[v]
                if dist.get(matched_to_v, float('inf')) == dist[u] + 1:
                    if dfs(matched_to_v):
                        pair_v[v] = u
                        pair_u[u] = v
                        return True

        dist[u] = float('inf')
        return False

    # Hopcroft-Karp main loop
    while bfs():
        for u in left:
            if pair_u[u] is None:
                dfs(u)

    # Return only the matched pairs (filter out None values)
    matching = {u: v for u, v in pair_u.items() if v is not None}
    return matching


def maximum_bipartite_matching(
    graph: Graph,
    left: Set[str],
    right: Set[str]
) -> Set[Tuple[str, str]]:
    """
    Find maximum matching in a bipartite graph.

    Wrapper around hopcroft_karp that returns matching as a set of edge tuples.

    Args:
        graph: Bipartite graph
        left: Set of vertex IDs in the left partition
        right: Set of vertex IDs in the right partition

    Returns:
        Set of (left_vertex, right_vertex) tuples representing the matching

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.builder().add_bipartite(['A', 'B'], ['X', 'Y'], complete=True).build()
        >>> left = {'A', 'B'}
        >>> right = {'X', 'Y'}
        >>> matching = maximum_bipartite_matching(g, left, right)
        >>> len(matching)
        2
    """
    matching_dict = hopcroft_karp(graph, left, right)
    return {(u, v) for u, v in matching_dict.items()}


def is_perfect_matching(
    graph: Graph,
    left: Set[str],
    right: Set[str]
) -> bool:
    """
    Check if a perfect matching exists in a bipartite graph.

    A perfect matching is a matching that covers all vertices.

    Args:
        graph: Bipartite graph
        left: Set of vertex IDs in the left partition
        right: Set of vertex IDs in the right partition

    Returns:
        True if a perfect matching exists

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.builder().add_bipartite(['A', 'B'], ['X', 'Y'], complete=True).build()
        >>> is_perfect_matching(g, {'A', 'B'}, {'X', 'Y'})
        True
    """
    if len(left) != len(right):
        return False

    matching = hopcroft_karp(graph, left, right)
    return len(matching) == len(left)


def maximum_matching(graph: Graph) -> Set[Tuple[str, str]]:
    """
    Find maximum matching in a general graph.

    For bipartite graphs, uses Hopcroft-Karp.
    For general graphs, uses a greedy approximation.

    Args:
        graph: Input graph

    Returns:
        Set of (vertex1, vertex2) tuples representing the matching

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.from_edges(('A', 'B'), ('C', 'D'), directed=False)
        >>> matching = maximum_matching(g)
        >>> len(matching)
        2

    Note:
        For general (non-bipartite) graphs, this uses a greedy approximation.
        For optimal matching in general graphs, use Edmond's Blossom algorithm
        (not yet implemented).
    """
    from .connectivity import is_bipartite

    # Check if graph is bipartite
    if is_bipartite(graph):
        # Extract bipartition
        coloring = {}
        visited = set()

        # BFS to color vertices
        for start in graph.vertices:
            if start.id in visited:
                continue

            queue = deque([start.id])
            coloring[start.id] = 0
            visited.add(start.id)

            while queue:
                current_id = queue.popleft()
                current_color = coloring[current_id]

                for neighbor_id in graph.neighbors(current_id):
                    if neighbor_id not in visited:
                        coloring[neighbor_id] = 1 - current_color
                        visited.add(neighbor_id)
                        queue.append(neighbor_id)

        # Split into left and right partitions
        left = {v_id for v_id, color in coloring.items() if color == 0}
        right = {v_id for v_id, color in coloring.items() if color == 1}

        # Use Hopcroft-Karp
        return maximum_bipartite_matching(graph, left, right)
    else:
        # Greedy matching for general graphs
        return _greedy_matching(graph)


def _greedy_matching(graph: Graph) -> Set[Tuple[str, str]]:
    """
    Greedy approximation for maximum matching.

    Iterates through edges and adds them to the matching if neither
    endpoint is already matched.

    Args:
        graph: Input graph

    Returns:
        Set of matched edge tuples
    """
    matching = set()
    matched_vertices = set()

    # Sort edges by weight (prefer higher weights if available)
    edges = sorted(graph.edges, key=lambda e: -e.weight)

    for edge in edges:
        if edge.source not in matched_vertices and edge.target not in matched_vertices:
            matching.add((edge.source, edge.target))
            matched_vertices.add(edge.source)
            matched_vertices.add(edge.target)

    return matching


def matching_size(matching: Set[Tuple[str, str]]) -> int:
    """
    Get the size (cardinality) of a matching.

    Args:
        matching: Set of matched edge tuples

    Returns:
        Number of edges in the matching

    Example:
        >>> matching = {('A', 'B'), ('C', 'D')}
        >>> matching_size(matching)
        2
    """
    return len(matching)


def is_maximal_matching(graph: Graph, matching: Set[Tuple[str, str]]) -> bool:
    """
    Check if a matching is maximal (cannot be extended).

    A matching is maximal if no edge can be added without violating
    the matching property.

    Args:
        graph: Input graph
        matching: Set of matched edge tuples

    Returns:
        True if the matching is maximal

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.from_edges(('A', 'B'), ('C', 'D'), directed=False)
        >>> matching = {('A', 'B')}
        >>> is_maximal_matching(g, matching)
        False
    """
    matched_vertices = set()
    for u, v in matching:
        matched_vertices.add(u)
        matched_vertices.add(v)

    # Try to find an edge that can be added
    for edge in graph.edges:
        if edge.source not in matched_vertices and edge.target not in matched_vertices:
            return False

    return True
