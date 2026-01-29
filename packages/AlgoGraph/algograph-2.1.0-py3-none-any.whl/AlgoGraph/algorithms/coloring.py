"""
Graph coloring algorithms.

Provides algorithms for vertex and edge coloring:
- Greedy Coloring: Simple greedy vertex coloring
- Welsh-Powell: Greedy coloring with vertex ordering
- Chromatic Number: Estimate the chromatic number
- Edge Coloring: Color edges of a graph
"""

from typing import Dict, Set, List, Optional

from AlgoGraph.graph import Graph


def greedy_coloring(
    graph: Graph,
    order: Optional[List[str]] = None
) -> Dict[str, int]:
    """
    Greedy vertex coloring algorithm.

    Colors vertices using the smallest available color, processing vertices
    in the given order (or arbitrary order if not specified).

    Args:
        graph: Input graph
        order: Optional list of vertex IDs specifying coloring order

    Returns:
        Dict mapping vertex ID to color (integer starting from 0)

    Example:
        >>> from AlgoGraph import Graph
        >>> # Triangle graph needs 3 colors
        >>> g = Graph.builder().add_cycle('A', 'B', 'C', directed=False).build()
        >>> coloring = greedy_coloring(g)
        >>> len(set(coloring.values()))  # Number of colors used
        3

    Note:
        The greedy algorithm does not guarantee optimal coloring.
        The number of colors used depends on the vertex ordering.
    """
    if graph.vertex_count == 0:
        return {}

    coloring = {}

    # Determine vertex order
    if order is None:
        order = [v.id for v in graph.vertices]

    for v_id in order:
        # Find colors used by neighbors
        neighbor_colors = {coloring.get(n_id) for n_id in graph.neighbors(v_id)
                          if n_id in coloring}

        # Find smallest available color
        color = 0
        while color in neighbor_colors:
            color += 1

        coloring[v_id] = color

    return coloring


def welsh_powell(graph: Graph) -> Dict[str, int]:
    """
    Welsh-Powell vertex coloring algorithm.

    Greedy coloring with vertices ordered by decreasing degree.
    Typically produces better colorings than random ordering.

    Args:
        graph: Input graph

    Returns:
        Dict mapping vertex ID to color

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.builder().add_complete('A', 'B', 'C', 'D').build()
        >>> coloring = welsh_powell(g)
        >>> len(set(coloring.values()))  # Complete graph needs n colors
        4

    References:
        Welsh, D. J. A., & Powell, M. B. (1967).
        An upper bound for the chromatic number of a graph and its application
        to timetabling problems.
    """
    if graph.vertex_count == 0:
        return {}

    # Sort vertices by degree (descending)
    vertices_by_degree = sorted(
        graph.vertices,
        key=lambda v: graph.degree(v.id),
        reverse=True
    )

    order = [v.id for v in vertices_by_degree]
    return greedy_coloring(graph, order)


def chromatic_number(graph: Graph) -> int:
    """
    Estimate the chromatic number of a graph.

    The chromatic number is the minimum number of colors needed to properly
    color the graph. This function uses Welsh-Powell to get an upper bound.

    Args:
        graph: Input graph

    Returns:
        Upper bound on chromatic number (may not be optimal)

    Example:
        >>> from AlgoGraph import Graph
        >>> # Bipartite graph has chromatic number 2
        >>> g = Graph.builder().add_bipartite(['A', 'B'], ['X', 'Y'], complete=True).build()
        >>> chromatic_number(g)
        2

    Note:
        Finding the exact chromatic number is NP-complete.
        This returns an upper bound using Welsh-Powell coloring.
    """
    if graph.vertex_count == 0:
        return 0

    coloring = welsh_powell(graph)
    return len(set(coloring.values()))


def is_valid_coloring(graph: Graph, coloring: Dict[str, int]) -> bool:
    """
    Check if a coloring is valid (no adjacent vertices have the same color).

    Args:
        graph: Input graph
        coloring: Dict mapping vertex ID to color

    Returns:
        True if coloring is valid

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.from_edges(('A', 'B'), directed=False)
        >>> coloring = {'A': 0, 'B': 1}
        >>> is_valid_coloring(g, coloring)
        True
        >>> bad_coloring = {'A': 0, 'B': 0}
        >>> is_valid_coloring(g, bad_coloring)
        False
    """
    for edge in graph.edges:
        color_u = coloring.get(edge.source)
        color_v = coloring.get(edge.target)

        if color_u is None or color_v is None:
            continue

        if color_u == color_v:
            return False

    return True


def dsatur(graph: Graph) -> Dict[str, int]:
    """
    DSatur (Degree of Saturation) vertex coloring algorithm.

    Colors vertices in order of decreasing saturation degree (number of
    different colors in the neighborhood). Breaks ties by degree.

    Often produces better colorings than simple greedy approaches.

    Args:
        graph: Input graph

    Returns:
        Dict mapping vertex ID to color

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.builder().add_cycle('A', 'B', 'C', 'D', directed=False).build()
        >>> coloring = dsatur(g)
        >>> is_valid_coloring(g, coloring)
        True

    References:
        Brélaz, D. (1979).
        New methods to color the vertices of a graph.
        Communications of the ACM, 22(4), 251-256.
    """
    if graph.vertex_count == 0:
        return {}

    coloring = {}
    uncolored = {v.id for v in graph.vertices}

    while uncolored:
        # Find vertex with highest saturation degree
        max_sat = -1
        max_degree = -1
        next_vertex = None

        for v_id in uncolored:
            # Saturation degree: number of different colors in neighborhood
            neighbor_colors = {coloring.get(n_id) for n_id in graph.neighbors(v_id)
                             if n_id in coloring}
            neighbor_colors.discard(None)
            sat = len(neighbor_colors)

            # Degree in uncolored subgraph
            degree = sum(1 for n_id in graph.neighbors(v_id) if n_id in uncolored)

            # Choose vertex with max saturation, breaking ties by degree
            if sat > max_sat or (sat == max_sat and degree > max_degree):
                max_sat = sat
                max_degree = degree
                next_vertex = v_id

        if next_vertex is None:
            next_vertex = uncolored.pop()
            uncolored.add(next_vertex)

        # Color the selected vertex
        neighbor_colors = {coloring.get(n_id) for n_id in graph.neighbors(next_vertex)
                          if n_id in coloring}
        neighbor_colors.discard(None)

        color = 0
        while color in neighbor_colors:
            color += 1

        coloring[next_vertex] = color
        uncolored.remove(next_vertex)

    return coloring


def edge_coloring(graph: Graph) -> Dict[tuple, int]:
    """
    Greedy edge coloring algorithm.

    Colors edges so that no two adjacent edges have the same color.
    Two edges are adjacent if they share a vertex.

    Args:
        graph: Input graph

    Returns:
        Dict mapping (source, target) tuples to colors

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.builder().add_path('A', 'B', 'C', directed=False).build()
        >>> coloring = edge_coloring(g)
        >>> len(coloring) == g.edge_count
        True

    Note:
        By Vizing's theorem, the chromatic index (edge chromatic number)
        is either Δ or Δ+1, where Δ is the maximum degree.
    """
    coloring = {}

    for edge in graph.edges:
        # Find colors used by adjacent edges
        adjacent_colors = set()

        # Edges adjacent to source
        for neighbor in graph.neighbors(edge.source):
            key = (edge.source, neighbor)
            if key in coloring:
                adjacent_colors.add(coloring[key])
            key_rev = (neighbor, edge.source)
            if key_rev in coloring:
                adjacent_colors.add(coloring[key_rev])

        # Edges adjacent to target
        for neighbor in graph.neighbors(edge.target):
            key = (edge.target, neighbor)
            if key in coloring:
                adjacent_colors.add(coloring[key])
            key_rev = (neighbor, edge.target)
            if key_rev in coloring:
                adjacent_colors.add(coloring[key_rev])

        # Find smallest available color
        color = 0
        while color in adjacent_colors:
            color += 1

        coloring[(edge.source, edge.target)] = color

    return coloring


def chromatic_index(graph: Graph) -> int:
    """
    Estimate the chromatic index (edge chromatic number).

    The chromatic index is the minimum number of colors needed to properly
    color the edges. By Vizing's theorem, it's either Δ or Δ+1 where Δ is
    the maximum degree.

    Args:
        graph: Input graph

    Returns:
        Upper bound on chromatic index

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.builder().add_star('center', 'A', 'B', 'C').build()
        >>> chromatic_index(g)
        3
    """
    if graph.edge_count == 0:
        return 0

    coloring = edge_coloring(graph)
    return len(set(coloring.values()))


def is_k_colorable(graph: Graph, k: int) -> bool:
    """
    Check if graph can be colored with k colors.

    Uses greedy coloring; returns False if more than k colors are needed.

    Args:
        graph: Input graph
        k: Number of colors

    Returns:
        True if graph can be colored with <= k colors (approximate)

    Example:
        >>> from AlgoGraph import Graph
        >>> # Bipartite graphs are 2-colorable
        >>> g = Graph.builder().add_bipartite(['A'], ['B'], complete=True).build()
        >>> is_k_colorable(g, 2)
        True

    Note:
        This uses greedy coloring, so it may return False even if the graph
        is k-colorable (k-coloring is NP-complete to verify optimally).
    """
    coloring = welsh_powell(graph)
    num_colors = len(set(coloring.values()))
    return num_colors <= k
