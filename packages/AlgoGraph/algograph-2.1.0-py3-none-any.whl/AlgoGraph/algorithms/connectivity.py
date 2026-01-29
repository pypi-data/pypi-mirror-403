"""
Graph connectivity algorithms.

Provides algorithms for analyzing graph connectivity:
- Connected components (undirected graphs)
- Strongly connected components (directed graphs)
- Connectivity checking
- Bipartiteness checking
"""

from typing import Set, List, Dict, Optional, Tuple
from collections import deque

from AlgoGraph.graph import Graph


def connected_components(graph: Graph) -> List[Set[str]]:
    """
    Find connected components in undirected graph.

    Args:
        graph: Undirected graph

    Returns:
        List of sets, each containing vertex IDs in a component

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C'), Vertex('D')},
        ...           {Edge('A', 'B', directed=False), Edge('C', 'D', directed=False)})
        >>> components = connected_components(g)
        >>> len(components)
        2
    """
    visited = set()
    components = []

    def dfs(vertex_id: str, component: Set[str]):
        if vertex_id in visited:
            return

        visited.add(vertex_id)
        component.add(vertex_id)

        for neighbor in graph.neighbors(vertex_id):
            dfs(neighbor, component)

    for vertex in graph.vertices:
        if vertex.id not in visited:
            component = set()
            dfs(vertex.id, component)
            components.append(component)

    return components


def is_connected(graph: Graph) -> bool:
    """
    Check if graph is connected.

    For directed graphs, checks weak connectivity (ignoring edge directions).

    Args:
        graph: Graph to check

    Returns:
        True if graph is connected

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B')}, {Edge('A', 'B')})
        >>> is_connected(g)
        True
    """
    if graph.vertex_count == 0:
        return True

    # For directed graphs, we need to check weak connectivity
    # Build undirected adjacency
    neighbors_map = {v.id: set() for v in graph.vertices}
    for edge in graph.edges:
        neighbors_map[edge.source].add(edge.target)
        neighbors_map[edge.target].add(edge.source)  # Treat as undirected

    # BFS/DFS from first vertex
    start = next(iter(graph.vertices)).id
    visited = set()
    stack = [start]

    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for neighbor in neighbors_map[v]:
            if neighbor not in visited:
                stack.append(neighbor)

    return len(visited) == graph.vertex_count


def strongly_connected_components(graph: Graph) -> List[Set[str]]:
    """
    Find strongly connected components in directed graph.

    Uses Kosaraju's algorithm.

    Args:
        graph: Directed graph

    Returns:
        List of sets, each containing vertex IDs in a strongly connected component

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B'), Edge('B', 'C'), Edge('C', 'A')})
        >>> sccs = strongly_connected_components(g)
        >>> len(sccs)
        1
    """
    # Step 1: DFS to get finish times
    visited = set()
    finish_stack = []

    def dfs1(vertex_id: str):
        if vertex_id in visited:
            return

        visited.add(vertex_id)

        for neighbor in graph.neighbors(vertex_id):
            dfs1(neighbor)

        finish_stack.append(vertex_id)

    for vertex in graph.vertices:
        if vertex.id not in visited:
            dfs1(vertex.id)

    # Step 2: Create transpose graph (reverse all edges)
    transpose_neighbors = {v.id: set() for v in graph.vertices}
    for edge in graph.edges:
        if edge.directed:
            transpose_neighbors[edge.target].add(edge.source)
        else:
            transpose_neighbors[edge.target].add(edge.source)
            transpose_neighbors[edge.source].add(edge.target)

    # Step 3: DFS on transpose in reverse finish time order
    visited.clear()
    sccs = []

    def dfs2(vertex_id: str, component: Set[str]):
        if vertex_id in visited:
            return

        visited.add(vertex_id)
        component.add(vertex_id)

        for neighbor in transpose_neighbors[vertex_id]:
            dfs2(neighbor, component)

    while finish_stack:
        vertex_id = finish_stack.pop()
        if vertex_id not in visited:
            component = set()
            dfs2(vertex_id, component)
            sccs.append(component)

    return sccs


def is_strongly_connected(graph: Graph) -> bool:
    """
    Check if directed graph is strongly connected.

    Args:
        graph: Directed graph

    Returns:
        True if graph is strongly connected

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B')},
        ...           {Edge('A', 'B'), Edge('B', 'A')})
        >>> is_strongly_connected(g)
        True
    """
    if graph.vertex_count == 0:
        return True

    sccs = strongly_connected_components(graph)
    return len(sccs) == 1


def is_bipartite(graph: Graph) -> Tuple[bool, Dict[str, int]]:
    """
    Check if graph is bipartite and return vertex coloring.

    A graph is bipartite if vertices can be colored with two colors
    such that no adjacent vertices have the same color.

    Args:
        graph: Graph to check

    Returns:
        Tuple of (is_bipartite, coloring)
        - is_bipartite: True if graph is bipartite
        - coloring: Dict mapping vertex ID to color (0 or 1)

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C'), Vertex('D')},
        ...           {Edge('A', 'B', directed=False), Edge('B', 'C', directed=False),
        ...            Edge('C', 'D', directed=False), Edge('D', 'A', directed=False)})
        >>> is_bip, coloring = is_bipartite(g)
        >>> is_bip
        True
    """
    coloring = {}

    def bfs_color(start: str) -> bool:
        """BFS to 2-color component starting from start."""
        queue = deque([start])
        coloring[start] = 0

        while queue:
            vertex_id = queue.popleft()
            current_color = coloring[vertex_id]
            next_color = 1 - current_color

            for neighbor in graph.neighbors(vertex_id):
                if neighbor in coloring:
                    # Check if coloring is consistent
                    if coloring[neighbor] != next_color:
                        return False
                else:
                    # Color neighbor with opposite color
                    coloring[neighbor] = next_color
                    queue.append(neighbor)

        return True

    # Try to color all components
    for vertex in graph.vertices:
        if vertex.id not in coloring:
            if not bfs_color(vertex.id):
                return False, {}

    return True, coloring


def find_bridges(graph: Graph) -> List[Tuple[str, str]]:
    """
    Find all bridges (cut edges) in undirected graph.

    A bridge is an edge whose removal increases the number of connected components.

    Args:
        graph: Undirected graph

    Returns:
        List of bridges as (u, v) tuples

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', directed=False), Edge('B', 'C', directed=False)})
        >>> bridges = find_bridges(g)
        >>> len(bridges)
        2
    """
    visited = set()
    discovery_time = {}
    low = {}
    parent = {}
    time = [0]
    bridges = []

    def dfs(u: str):
        visited.add(u)
        discovery_time[u] = low[u] = time[0]
        time[0] += 1

        for v in graph.neighbors(u):
            if v not in visited:
                parent[v] = u
                dfs(v)

                # Update low value
                low[u] = min(low[u], low[v])

                # Check if edge is a bridge
                if low[v] > discovery_time[u]:
                    bridges.append((u, v))

            elif v != parent.get(u):
                # Update low value for back edge
                low[u] = min(low[u], discovery_time[v])

    for vertex in graph.vertices:
        if vertex.id not in visited:
            dfs(vertex.id)

    return bridges


def find_articulation_points(graph: Graph) -> Set[str]:
    """
    Find all articulation points (cut vertices) in undirected graph.

    An articulation point is a vertex whose removal increases the number of
    connected components.

    Args:
        graph: Undirected graph

    Returns:
        Set of vertex IDs that are articulation points

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', directed=False), Edge('B', 'C', directed=False)})
        >>> aps = find_articulation_points(g)
        >>> 'B' in aps
        True
    """
    visited = set()
    discovery_time = {}
    low = {}
    parent = {}
    time = [0]
    articulation_points = set()

    def dfs(u: str):
        children = 0
        visited.add(u)
        discovery_time[u] = low[u] = time[0]
        time[0] += 1

        for v in graph.neighbors(u):
            if v not in visited:
                children += 1
                parent[v] = u
                dfs(v)

                # Update low value
                low[u] = min(low[u], low[v])

                # Check if u is an articulation point
                if parent.get(u) is None and children > 1:
                    # Root with multiple children
                    articulation_points.add(u)
                elif parent.get(u) is not None and low[v] >= discovery_time[u]:
                    # Non-root
                    articulation_points.add(u)

            elif v != parent.get(u):
                # Update low value for back edge
                low[u] = min(low[u], discovery_time[v])

    for vertex in graph.vertices:
        if vertex.id not in visited:
            parent[vertex.id] = None
            dfs(vertex.id)

    return articulation_points


def is_tree(graph: Graph) -> bool:
    """
    Check if graph is a tree.

    A graph is a tree if it's connected and acyclic with |V| - 1 edges.

    Args:
        graph: Graph to check

    Returns:
        True if graph is a tree

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B', directed=False), Edge('B', 'C', directed=False)})
        >>> is_tree(g)
        True
    """
    if graph.vertex_count == 0:
        return True

    # Tree must have |V| - 1 edges
    if graph.edge_count != graph.vertex_count - 1:
        return False

    # Tree must be connected
    return is_connected(graph)


def diameter(graph: Graph) -> int:
    """
    Find diameter of graph (longest shortest path).

    Args:
        graph: Graph to analyze

    Returns:
        Length of longest shortest path

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B'), Edge('B', 'C')})
        >>> diameter(g)
        2
    """
    from .shortest_path import floyd_warshall

    dist = floyd_warshall(graph)
    max_dist = 0

    for (u, v), d in dist.items():
        if d != float('inf') and d > max_dist:
            max_dist = int(d)

    return max_dist
