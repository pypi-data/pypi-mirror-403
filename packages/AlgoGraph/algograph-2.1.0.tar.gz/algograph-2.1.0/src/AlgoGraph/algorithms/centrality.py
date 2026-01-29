"""
Centrality algorithms for measuring vertex importance.

Provides algorithms for computing various centrality measures:
- PageRank: Google's page ranking algorithm
- Betweenness Centrality: Identifies bridge vertices
- Closeness Centrality: Measures average distance to all vertices
- Degree Centrality: Simple measure based on number of connections
"""

from typing import Dict, Set, List, Optional, Tuple
from collections import deque

from AlgoGraph.graph import Graph


def pagerank(
    graph: Graph,
    damping: float = 0.85,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> Dict[str, float]:
    """
    Compute PageRank scores for all vertices.

    PageRank is Google's famous algorithm for ranking web pages.
    It measures importance by counting the number and quality of links.

    Args:
        graph: Input graph
        damping: Damping factor (probability of following a link) (default: 0.85)
        max_iterations: Maximum number of iterations (default: 100)
        tolerance: Convergence tolerance (default: 1e-6)

    Returns:
        Dict mapping vertex ID to PageRank score

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'A'))
        >>> scores = pagerank(g)
        >>> all(0 < score < 1 for score in scores.values())
        True

    References:
        Page, L., Brin, S., Motwani, R., & Winograd, T. (1999).
        The PageRank citation ranking: Bringing order to the web.
    """
    if graph.vertex_count == 0:
        return {}

    # Initialize PageRank scores uniformly
    n = graph.vertex_count
    pagerank_scores = {v.id: 1.0 / n for v in graph.vertices}

    # Build incoming edges map
    incoming = {v.id: set() for v in graph.vertices}
    outgoing_count = {v.id: 0 for v in graph.vertices}

    for edge in graph.edges:
        if edge.directed:
            incoming[edge.target].add(edge.source)
            outgoing_count[edge.source] += 1
        else:
            # Undirected edges: both directions
            incoming[edge.target].add(edge.source)
            incoming[edge.source].add(edge.target)
            outgoing_count[edge.source] += 1
            outgoing_count[edge.target] += 1

    # Dangling nodes (no outgoing edges) distribute equally
    dangling = [v.id for v in graph.vertices if outgoing_count[v.id] == 0]

    # Power iteration
    for _ in range(max_iterations):
        new_scores = {}
        dangling_sum = sum(pagerank_scores[vid] for vid in dangling)

        for v in graph.vertices:
            # Contribution from random jump
            rank = (1 - damping) / n

            # Contribution from dangling nodes
            rank += damping * dangling_sum / n

            # Contribution from incoming edges
            for neighbor_id in incoming[v.id]:
                rank += damping * pagerank_scores[neighbor_id] / outgoing_count[neighbor_id]

            new_scores[v.id] = rank

        # Check convergence
        diff = sum(abs(new_scores[vid] - pagerank_scores[vid]) for vid in pagerank_scores)
        pagerank_scores = new_scores

        if diff < tolerance:
            break

    return pagerank_scores


def betweenness_centrality(
    graph: Graph,
    normalized: bool = True
) -> Dict[str, float]:
    """
    Compute betweenness centrality for all vertices.

    Betweenness centrality measures how often a vertex lies on the shortest
    path between other vertices. High betweenness indicates a "bridge" vertex.

    Uses Brandes' algorithm for efficiency: O(V*E) for unweighted graphs.

    Args:
        graph: Input graph
        normalized: If True, normalize scores by the number of vertex pairs (default: True)

    Returns:
        Dict mapping vertex ID to betweenness centrality score

    Example:
        >>> from AlgoGraph import Graph
        >>> # Bridge graph: A-B-C where B is the bridge
        >>> g = Graph.from_edges(('A', 'B'), ('B', 'C'), directed=False)
        >>> bc = betweenness_centrality(g)
        >>> bc['B'] > bc['A']  # B has higher betweenness
        True

    References:
        Brandes, U. (2001). A faster algorithm for betweenness centrality.
        Journal of Mathematical Sociology, 25(2), 163-177.
    """
    if graph.vertex_count == 0:
        return {}

    betweenness = {v.id: 0.0 for v in graph.vertices}

    # Brandes' algorithm
    for source in graph.vertices:
        # BFS to find shortest paths
        stack = []
        predecessors = {v.id: [] for v in graph.vertices}
        sigma = {v.id: 0 for v in graph.vertices}
        sigma[source.id] = 1
        distance = {v.id: -1 for v in graph.vertices}
        distance[source.id] = 0

        queue = deque([source.id])

        while queue:
            v_id = queue.popleft()
            stack.append(v_id)

            for w_id in graph.neighbors(v_id):
                # First time we see w?
                if distance[w_id] < 0:
                    queue.append(w_id)
                    distance[w_id] = distance[v_id] + 1

                # Shortest path to w via v?
                if distance[w_id] == distance[v_id] + 1:
                    sigma[w_id] += sigma[v_id]
                    predecessors[w_id].append(v_id)

        # Accumulation: back-propagate dependencies
        delta = {v.id: 0.0 for v in graph.vertices}

        while stack:
            w_id = stack.pop()
            for v_id in predecessors[w_id]:
                delta[v_id] += (sigma[v_id] / sigma[w_id]) * (1 + delta[w_id])

            if w_id != source.id:
                betweenness[w_id] += delta[w_id]

    # Normalization
    if normalized and graph.vertex_count > 2:
        # For undirected graphs: normalize by (n-1)(n-2)/2
        # For directed graphs: normalize by (n-1)(n-2)
        n = graph.vertex_count
        if graph.is_undirected:
            scale = 2.0 / ((n - 1) * (n - 2))
        else:
            scale = 1.0 / ((n - 1) * (n - 2))

        betweenness = {vid: bc * scale for vid, bc in betweenness.items()}

    return betweenness


def closeness_centrality(
    graph: Graph,
    normalized: bool = True
) -> Dict[str, float]:
    """
    Compute closeness centrality for all vertices.

    Closeness centrality measures how close a vertex is to all other vertices.
    It's the reciprocal of the average shortest path distance.

    Args:
        graph: Input graph
        normalized: If True, normalize by (n-1) where n is number of vertices (default: True)

    Returns:
        Dict mapping vertex ID to closeness centrality score
        Returns 0.0 for vertices that cannot reach all others

    Example:
        >>> from AlgoGraph import Graph
        >>> # Star graph: center has highest closeness
        >>> g = Graph.builder().add_star('center', 'A', 'B', 'C').build()
        >>> cc = closeness_centrality(g)
        >>> cc['center'] > cc['A']  # Center has higher closeness
        True

    Note:
        For disconnected graphs, uses the Wasserman-Faust formula:
        C(v) = (n-1) / (N-1) * (n-1) / sum(distances)
        where n is the number of reachable vertices and N is total vertices.
    """
    if graph.vertex_count == 0:
        return {}

    closeness = {}

    for source in graph.vertices:
        # BFS to find distances to all other vertices
        distances = {v.id: float('inf') for v in graph.vertices}
        distances[source.id] = 0

        queue = deque([source.id])

        while queue:
            current_id = queue.popleft()
            current_dist = distances[current_id]

            for neighbor_id in graph.neighbors(current_id):
                if distances[neighbor_id] == float('inf'):
                    distances[neighbor_id] = current_dist + 1
                    queue.append(neighbor_id)

        # Calculate closeness
        reachable = [d for d in distances.values() if d != float('inf') and d > 0]

        if not reachable:
            # Isolated vertex
            closeness[source.id] = 0.0
        else:
            # Sum of distances to reachable vertices
            total_distance = sum(reachable)
            n_reachable = len(reachable)

            if total_distance > 0:
                # Basic closeness: reciprocal of average distance
                cc = n_reachable / total_distance

                # Wasserman-Faust normalization for disconnected graphs
                if normalized and graph.vertex_count > 1:
                    cc *= n_reachable / (graph.vertex_count - 1)

                closeness[source.id] = cc
            else:
                closeness[source.id] = 0.0

    return closeness


def degree_centrality(
    graph: Graph,
    normalized: bool = True
) -> Dict[str, float]:
    """
    Compute degree centrality for all vertices.

    Degree centrality is the simplest centrality measure: the number of edges
    connected to a vertex. For directed graphs, uses out-degree.

    Args:
        graph: Input graph
        normalized: If True, normalize by (n-1) where n is number of vertices (default: True)

    Returns:
        Dict mapping vertex ID to degree centrality score

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.from_edges(('A', 'B'), ('A', 'C'), ('A', 'D'))
        >>> dc = degree_centrality(g)
        >>> dc['A'] > dc['B']  # A has highest degree
        True
    """
    if graph.vertex_count == 0:
        return {}

    degree_cent = {}

    for v in graph.vertices:
        degree = graph.degree(v.id)

        if normalized and graph.vertex_count > 1:
            # Normalize by maximum possible degree
            degree_cent[v.id] = degree / (graph.vertex_count - 1)
        else:
            degree_cent[v.id] = float(degree)

    return degree_cent


def eigenvector_centrality(
    graph: Graph,
    max_iterations: int = 100,
    tolerance: float = 1e-6
) -> Dict[str, float]:
    """
    Compute eigenvector centrality for all vertices.

    Eigenvector centrality measures influence based on connections to
    well-connected vertices. A vertex is important if connected to important vertices.

    Uses power iteration to find the dominant eigenvector of the adjacency matrix.

    Args:
        graph: Input graph (must be strongly connected for convergence)
        max_iterations: Maximum number of iterations (default: 100)
        tolerance: Convergence tolerance (default: 1e-6)

    Returns:
        Dict mapping vertex ID to eigenvector centrality score

    Example:
        >>> from AlgoGraph import Graph
        >>> g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'A'), directed=False)
        >>> ec = eigenvector_centrality(g)
        >>> all(0 <= score <= 1 for score in ec.values())
        True

    Note:
        May not converge for disconnected or directed acyclic graphs.
        Returns uniform scores in such cases.
    """
    if graph.vertex_count == 0:
        return {}

    # Initialize scores uniformly
    scores = {v.id: 1.0 / graph.vertex_count for v in graph.vertices}

    # Power iteration
    for _ in range(max_iterations):
        new_scores = {v.id: 0.0 for v in graph.vertices}

        # Each vertex's score is the sum of its neighbors' scores
        for v in graph.vertices:
            for neighbor_id in graph.neighbors(v.id):
                new_scores[v.id] += scores[neighbor_id]

        # Normalize
        norm = sum(new_scores.values())
        if norm == 0:
            # Disconnected or DAG - return uniform scores
            return {v.id: 1.0 / graph.vertex_count for v in graph.vertices}

        new_scores = {vid: score / norm for vid, score in new_scores.items()}

        # Check convergence
        diff = sum(abs(new_scores[vid] - scores[vid]) for vid in scores)
        scores = new_scores

        if diff < tolerance:
            break

    return scores
