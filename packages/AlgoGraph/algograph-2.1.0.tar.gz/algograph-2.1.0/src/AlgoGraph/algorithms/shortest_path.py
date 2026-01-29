"""
Shortest path algorithms.

Provides algorithms for finding shortest paths in weighted graphs:
- Dijkstra's algorithm (single-source, non-negative weights)
- Bellman-Ford algorithm (single-source, allows negative weights)
- Floyd-Warshall algorithm (all-pairs shortest paths)
"""

from typing import Dict, Optional, List, Tuple
import heapq

from AlgoGraph.graph import Graph


def dijkstra(
    graph: Graph,
    source: str
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Dijkstra's shortest path algorithm.

    Finds shortest paths from source to all other vertices.
    Requires non-negative edge weights.

    Args:
        graph: Graph with non-negative edge weights
        source: Source vertex ID

    Returns:
        Tuple of (distances, predecessors)
        - distances: Dict mapping vertex ID to shortest distance from source
        - predecessors: Dict mapping vertex ID to predecessor in shortest path

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', weight=2), Edge('B', 'C', weight=3)})
        >>> distances, predecessors = dijkstra(g, 'A')
        >>> distances['C']
        5.0
    """
    # Initialize distances
    distances = {v.id: float('inf') for v in graph.vertices}
    distances[source] = 0.0

    # Initialize predecessors
    predecessors = {v.id: None for v in graph.vertices}

    # Priority queue: (distance, vertex_id)
    pq = [(0.0, source)]
    visited = set()

    while pq:
        current_dist, current_id = heapq.heappop(pq)

        if current_id in visited:
            continue

        visited.add(current_id)

        # Skip if we found a better path already
        if current_dist > distances[current_id]:
            continue

        # Check all neighbors
        for neighbor_id in graph.neighbors(current_id):
            edge = graph.get_edge(current_id, neighbor_id)
            if edge is None:
                continue

            # Calculate distance through current vertex
            distance = distances[current_id] + edge.weight

            # Update if we found a shorter path
            if distance < distances[neighbor_id]:
                distances[neighbor_id] = distance
                predecessors[neighbor_id] = current_id
                heapq.heappush(pq, (distance, neighbor_id))

    return distances, predecessors


def reconstruct_path(
    predecessors: Dict[str, Optional[str]],
    source: str,
    target: str
) -> Optional[List[str]]:
    """
    Reconstruct path from predecessors dictionary.

    Args:
        predecessors: Predecessor dictionary from shortest path algorithm
        source: Source vertex ID
        target: Target vertex ID

    Returns:
        List of vertex IDs forming path from source to target, or None if no path

    Example:
        >>> predecessors = {'A': None, 'B': 'A', 'C': 'B'}
        >>> reconstruct_path(predecessors, 'A', 'C')
        ['A', 'B', 'C']
    """
    if target not in predecessors or predecessors[target] is None and target != source:
        return None

    path = []
    current = target

    while current is not None:
        path.append(current)
        current = predecessors[current]

    path.reverse()

    if path[0] != source:
        return None

    return path


def bellman_ford(
    graph: Graph,
    source: str
) -> Tuple[Dict[str, float], Dict[str, Optional[str]]]:
    """
    Bellman-Ford shortest path algorithm.

    Finds shortest paths from source to all other vertices.
    Works with negative edge weights and detects negative cycles.

    Args:
        graph: Graph (may have negative edge weights)
        source: Source vertex ID

    Returns:
        Tuple of (distances, predecessors)

    Raises:
        ValueError: If graph contains a negative cycle

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', weight=-1), Edge('B', 'C', weight=2)})
        >>> distances, predecessors = bellman_ford(g, 'A')
        >>> distances['C']
        1.0
    """
    # Initialize distances
    distances = {v.id: float('inf') for v in graph.vertices}
    distances[source] = 0.0

    # Initialize predecessors
    predecessors = {v.id: None for v in graph.vertices}

    # Relax edges |V| - 1 times
    for _ in range(graph.vertex_count - 1):
        for edge in graph.edges:
            u, v = edge.source, edge.target

            if distances[u] != float('inf'):
                new_distance = distances[u] + edge.weight

                if new_distance < distances[v]:
                    distances[v] = new_distance
                    predecessors[v] = u

    # Check for negative cycles
    for edge in graph.edges:
        u, v = edge.source, edge.target

        if distances[u] != float('inf'):
            if distances[u] + edge.weight < distances[v]:
                raise ValueError("Graph contains a negative cycle")

    return distances, predecessors


def floyd_warshall(graph: Graph) -> Dict[Tuple[str, str], float]:
    """
    Floyd-Warshall all-pairs shortest paths algorithm.

    Finds shortest paths between all pairs of vertices.

    Args:
        graph: Graph to analyze

    Returns:
        Dictionary mapping (source, target) tuples to shortest distance

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', weight=1), Edge('B', 'C', weight=2)})
        >>> dist = floyd_warshall(g)
        >>> dist[('A', 'C')]
        3.0
    """
    # Initialize distance matrix
    vertices = list(graph.vertices)
    vertex_ids = [v.id for v in vertices]

    dist = {}

    # Initialize with infinity
    for u_id in vertex_ids:
        for v_id in vertex_ids:
            if u_id == v_id:
                dist[(u_id, v_id)] = 0.0
            else:
                dist[(u_id, v_id)] = float('inf')

    # Set distances for edges
    for edge in graph.edges:
        dist[(edge.source, edge.target)] = edge.weight

        # For undirected edges, set both directions
        if not edge.directed:
            dist[(edge.target, edge.source)] = edge.weight

    # Floyd-Warshall algorithm
    for k_id in vertex_ids:
        for i_id in vertex_ids:
            for j_id in vertex_ids:
                if dist[(i_id, j_id)] > dist[(i_id, k_id)] + dist[(k_id, j_id)]:
                    dist[(i_id, j_id)] = dist[(i_id, k_id)] + dist[(k_id, j_id)]

    return dist


def a_star(
    graph: Graph,
    start: str,
    goal: str,
    heuristic: Dict[str, float]
) -> Optional[List[str]]:
    """
    A* search algorithm.

    Finds shortest path using heuristic function.

    Args:
        graph: Graph to search
        start: Starting vertex ID
        goal: Goal vertex ID
        heuristic: Dictionary mapping vertex ID to heuristic cost to goal

    Returns:
        Path from start to goal, or None if no path exists

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', weight=1), Edge('B', 'C', weight=1)})
        >>> h = {'A': 2, 'B': 1, 'C': 0}  # Heuristic: distance to C
        >>> a_star(g, 'A', 'C', h)
        ['A', 'B', 'C']
    """
    # g_score: cost from start to vertex
    g_score = {v.id: float('inf') for v in graph.vertices}
    g_score[start] = 0.0

    # f_score: g_score + heuristic
    f_score = {v.id: float('inf') for v in graph.vertices}
    f_score[start] = heuristic.get(start, 0)

    # Priority queue: (f_score, vertex_id)
    open_set = [(f_score[start], start)]
    came_from = {}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            return list(reversed(path))

        for neighbor in graph.neighbors(current):
            edge = graph.get_edge(current, neighbor)
            if edge is None:
                continue

            # Calculate tentative g_score
            tentative_g = g_score[current] + edge.weight

            if tentative_g < g_score[neighbor]:
                # This path is better
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic.get(neighbor, 0)

                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None


def shortest_path(
    graph: Graph,
    source: str,
    target: str
) -> Optional[List[str]]:
    """
    Find shortest path between two vertices.

    Uses Dijkstra's algorithm for non-negative weights.

    Args:
        graph: Graph to search
        source: Source vertex ID
        target: Target vertex ID

    Returns:
        Shortest path from source to target, or None if no path exists

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', weight=1), Edge('B', 'C', weight=2)})
        >>> shortest_path(g, 'A', 'C')
        ['A', 'B', 'C']
    """
    distances, predecessors = dijkstra(graph, source)

    if distances[target] == float('inf'):
        return None

    return reconstruct_path(predecessors, source, target)


def shortest_path_length(
    graph: Graph,
    source: str,
    target: str
) -> Optional[float]:
    """
    Find length of shortest path between two vertices.

    Args:
        graph: Graph to search
        source: Source vertex ID
        target: Target vertex ID

    Returns:
        Length of shortest path, or None if no path exists

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', weight=2), Edge('B', 'C', weight=3)})
        >>> shortest_path_length(g, 'A', 'C')
        5.0
    """
    distances, _ = dijkstra(graph, source)

    if distances[target] == float('inf'):
        return None

    return distances[target]


def all_shortest_paths(
    graph: Graph,
    source: str,
    target: str
) -> List[List[str]]:
    """
    Find all shortest paths between two vertices.

    Returns all paths with minimum length.

    Args:
        graph: Graph to search
        source: Source vertex ID
        target: Target vertex ID

    Returns:
        List of all shortest paths

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> # Graph with two paths of equal length
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C'), Vertex('D')},
        ...           {Edge('A', 'B', weight=1), Edge('A', 'C', weight=1),
        ...            Edge('B', 'D', weight=1), Edge('C', 'D', weight=1)})
        >>> paths = all_shortest_paths(g, 'A', 'D')
        >>> len(paths)
        2
    """
    # First find shortest distance
    distances, _ = dijkstra(graph, source)

    if distances[target] == float('inf'):
        return []

    shortest_dist = distances[target]
    all_paths = []

    # DFS to find all paths with that length
    def dfs(current: str, path: List[str], dist: float):
        if dist > shortest_dist:
            return

        if current == target:
            if dist == shortest_dist:
                all_paths.append(path.copy())
            return

        for neighbor in graph.neighbors(current):
            if neighbor not in path:  # Avoid cycles
                edge = graph.get_edge(current, neighbor)
                if edge:
                    path.append(neighbor)
                    dfs(neighbor, path, dist + edge.weight)
                    path.pop()

    dfs(source, [source], 0.0)
    return all_paths
