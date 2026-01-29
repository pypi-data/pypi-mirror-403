"""
Graph traversal algorithms.

Provides various methods for traversing graphs including:
- Depth-first search (DFS)
- Breadth-first search (BFS)
- Topological sort (for DAGs)
"""

from typing import Set, List, Dict, Callable, Optional
from collections import deque

from AlgoGraph.graph import Graph
from AlgoGraph.vertex import Vertex


def dfs(
    graph: Graph,
    start: str,
    visit: Optional[Callable[[str], None]] = None
) -> List[str]:
    """
    Depth-first search traversal.

    Args:
        graph: Graph to traverse
        start: Starting vertex ID
        visit: Optional callback function called for each visited vertex

    Returns:
        List of vertex IDs in DFS order

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B'), Edge('B', 'C')})
        >>> dfs(g, 'A')
        ['A', 'B', 'C']
    """
    visited = set()
    order = []

    def dfs_helper(vertex_id: str):
        if vertex_id in visited:
            return

        visited.add(vertex_id)
        order.append(vertex_id)

        if visit:
            visit(vertex_id)

        for neighbor in graph.neighbors(vertex_id):
            dfs_helper(neighbor)

    dfs_helper(start)
    return order


def dfs_recursive(
    graph: Graph,
    start: str,
    visited: Optional[Set[str]] = None
) -> List[str]:
    """
    Recursive depth-first search.

    Args:
        graph: Graph to traverse
        start: Starting vertex ID
        visited: Set of already visited vertices (for internal use)

    Returns:
        List of vertex IDs in DFS order
    """
    if visited is None:
        visited = set()

    if start in visited:
        return []

    visited.add(start)
    result = [start]

    for neighbor in graph.neighbors(start):
        result.extend(dfs_recursive(graph, neighbor, visited))

    return result


def dfs_iterative(graph: Graph, start: str) -> List[str]:
    """
    Iterative depth-first search using explicit stack.

    Args:
        graph: Graph to traverse
        start: Starting vertex ID

    Returns:
        List of vertex IDs in DFS order
    """
    visited = set()
    order = []
    stack = [start]

    while stack:
        vertex_id = stack.pop()

        if vertex_id in visited:
            continue

        visited.add(vertex_id)
        order.append(vertex_id)

        # Add neighbors in reverse order to maintain left-to-right traversal
        neighbors = list(graph.neighbors(vertex_id))
        for neighbor in reversed(neighbors):
            if neighbor not in visited:
                stack.append(neighbor)

    return order


def bfs(
    graph: Graph,
    start: str,
    visit: Optional[Callable[[str], None]] = None
) -> List[str]:
    """
    Breadth-first search traversal.

    Args:
        graph: Graph to traverse
        start: Starting vertex ID
        visit: Optional callback function called for each visited vertex

    Returns:
        List of vertex IDs in BFS order

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B'), Edge('A', 'C')})
        >>> bfs(g, 'A')
        ['A', 'B', 'C']
    """
    visited = set()
    order = []
    queue = deque([start])

    while queue:
        vertex_id = queue.popleft()

        if vertex_id in visited:
            continue

        visited.add(vertex_id)
        order.append(vertex_id)

        if visit:
            visit(vertex_id)

        for neighbor in graph.neighbors(vertex_id):
            if neighbor not in visited:
                queue.append(neighbor)

    return order


def bfs_levels(graph: Graph, start: str) -> List[List[str]]:
    """
    BFS traversal returning vertices grouped by level.

    Args:
        graph: Graph to traverse
        start: Starting vertex ID

    Returns:
        List of levels, where each level is a list of vertex IDs

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C'), Vertex('D')},
        ...           {Edge('A', 'B'), Edge('A', 'C'), Edge('B', 'D')})
        >>> bfs_levels(g, 'A')
        [['A'], ['B', 'C'], ['D']]
    """
    visited = set()
    levels = []
    current_level = [start]

    while current_level:
        levels.append(current_level)
        next_level = []

        for vertex_id in current_level:
            if vertex_id in visited:
                continue

            visited.add(vertex_id)

            for neighbor in graph.neighbors(vertex_id):
                if neighbor not in visited and neighbor not in next_level:
                    next_level.append(neighbor)

        current_level = next_level

    return levels


def topological_sort(graph: Graph) -> List[str]:
    """
    Topological sort of a directed acyclic graph (DAG).

    Returns vertices in topological order such that for every directed
    edge (u, v), u comes before v in the ordering.

    Args:
        graph: Directed acyclic graph

    Returns:
        List of vertex IDs in topological order

    Raises:
        ValueError: If graph contains a cycle

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> # Build dependency graph: A -> B -> C
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B'), Edge('B', 'C')})
        >>> topological_sort(g)
        ['A', 'B', 'C']
    """
    # Kahn's algorithm using in-degrees
    in_degree = {v.id: 0 for v in graph.vertices}

    # Calculate in-degrees
    for edge in graph.edges:
        if edge.directed:
            in_degree[edge.target] = in_degree.get(edge.target, 0) + 1

    # Queue of vertices with in-degree 0
    queue = deque([v_id for v_id, degree in in_degree.items() if degree == 0])
    result = []

    while queue:
        vertex_id = queue.popleft()
        result.append(vertex_id)

        # Reduce in-degree for neighbors
        for neighbor in graph.neighbors(vertex_id):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check for cycles
    if len(result) != graph.vertex_count:
        raise ValueError("Graph contains a cycle - cannot perform topological sort")

    return result


def topological_sort_dfs(graph: Graph) -> List[str]:
    """
    Topological sort using DFS.

    Alternative implementation using depth-first search.

    Args:
        graph: Directed acyclic graph

    Returns:
        List of vertex IDs in topological order

    Raises:
        ValueError: If graph contains a cycle
    """
    visited = set()
    temp_mark = set()  # For cycle detection
    result = []

    def visit(vertex_id: str):
        if vertex_id in temp_mark:
            raise ValueError("Graph contains a cycle - cannot perform topological sort")

        if vertex_id in visited:
            return

        temp_mark.add(vertex_id)

        for neighbor in graph.neighbors(vertex_id):
            visit(neighbor)

        temp_mark.remove(vertex_id)
        visited.add(vertex_id)
        result.append(vertex_id)

    for vertex in graph.vertices:
        if vertex.id not in visited:
            visit(vertex.id)

    # Reverse to get correct topological order
    return list(reversed(result))


def has_cycle(graph: Graph) -> bool:
    """
    Check if graph contains a cycle.

    Works for both directed and undirected graphs.

    Args:
        graph: Graph to check

    Returns:
        True if graph contains a cycle

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> # Acyclic graph
        >>> g1 = Graph({Vertex('A'), Vertex('B')}, {Edge('A', 'B')})
        >>> has_cycle(g1)
        False
        >>> # Cyclic graph
        >>> g2 = Graph({Vertex('A'), Vertex('B')},
        ...            {Edge('A', 'B'), Edge('B', 'A')})
        >>> has_cycle(g2)
        True
    """
    visited = set()
    rec_stack = set()

    def has_cycle_helper(vertex_id: str, parent: Optional[str] = None) -> bool:
        visited.add(vertex_id)
        rec_stack.add(vertex_id)

        for neighbor in graph.neighbors(vertex_id):
            if neighbor not in visited:
                if has_cycle_helper(neighbor, vertex_id):
                    return True
            elif neighbor in rec_stack:
                # For undirected graphs, ignore edge back to parent
                if graph.is_undirected and neighbor == parent:
                    continue
                return True

        rec_stack.remove(vertex_id)
        return False

    for vertex in graph.vertices:
        if vertex.id not in visited:
            if has_cycle_helper(vertex.id):
                return True

    return False


def find_path(graph: Graph, start: str, goal: str) -> Optional[List[str]]:
    """
    Find a path from start to goal using BFS.

    Args:
        graph: Graph to search
        start: Starting vertex ID
        goal: Goal vertex ID

    Returns:
        List of vertex IDs forming path from start to goal, or None if no path exists

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B'), Edge('B', 'C')})
        >>> find_path(g, 'A', 'C')
        ['A', 'B', 'C']
    """
    if start == goal:
        return [start]

    visited = set()
    queue = deque([(start, [start])])

    while queue:
        vertex_id, path = queue.popleft()

        if vertex_id in visited:
            continue

        visited.add(vertex_id)

        if vertex_id == goal:
            return path

        for neighbor in graph.neighbors(vertex_id):
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))

    return None


def find_all_paths(
    graph: Graph,
    start: str,
    goal: str,
    max_length: Optional[int] = None
) -> List[List[str]]:
    """
    Find all paths from start to goal.

    Args:
        graph: Graph to search
        start: Starting vertex ID
        goal: Goal vertex ID
        max_length: Maximum path length (optional)

    Returns:
        List of all paths (each path is a list of vertex IDs)

    Example:
        >>> from AlgoGraph import Graph, Edge, Vertex
        >>> g = Graph({Vertex('A'), Vertex('B'), Vertex('C')},
        ...           {Edge('A', 'B'), Edge('A', 'C'), Edge('B', 'C')})
        >>> paths = find_all_paths(g, 'A', 'C')
        >>> len(paths)
        2
    """
    all_paths = []

    def dfs_paths(current: str, path: List[str]):
        if max_length and len(path) > max_length:
            return

        if current == goal:
            all_paths.append(path.copy())
            return

        for neighbor in graph.neighbors(current):
            if neighbor not in path:  # Avoid cycles
                path.append(neighbor)
                dfs_paths(neighbor, path)
                path.pop()

    dfs_paths(start, [start])
    return all_paths
