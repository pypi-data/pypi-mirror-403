"""
Graph algorithms organized by category.

This package provides a comprehensive collection of graph algorithms including:
- Traversal algorithms (DFS, BFS, topological sort)
- Shortest path algorithms (Dijkstra, Bellman-Ford, Floyd-Warshall, A*)
- Connectivity algorithms (components, bridges, articulation points)
- Spanning tree algorithms (Kruskal, Prim)
- Centrality algorithms (PageRank, betweenness, closeness, eigenvector)
- Flow network algorithms (max flow, min cut, Edmonds-Karp)
- Matching algorithms (Hopcroft-Karp, maximum bipartite matching)
- Graph coloring algorithms (greedy, Welsh-Powell, DSatur)
"""

from .traversal import (
    dfs,
    dfs_recursive,
    dfs_iterative,
    bfs,
    bfs_levels,
    topological_sort,
    topological_sort_dfs,
    has_cycle,
    find_path,
    find_all_paths,
)

from .shortest_path import (
    dijkstra,
    bellman_ford,
    floyd_warshall,
    a_star,
    shortest_path,
    shortest_path_length,
    all_shortest_paths,
    reconstruct_path,
)

from .connectivity import (
    connected_components,
    is_connected,
    strongly_connected_components,
    is_strongly_connected,
    is_bipartite,
    find_bridges,
    find_articulation_points,
    is_tree,
    diameter,
)

from .spanning_tree import (
    kruskal,
    prim,
    minimum_spanning_tree,
    total_weight,
    is_spanning_tree,
)

from .centrality import (
    pagerank,
    betweenness_centrality,
    closeness_centrality,
    degree_centrality,
    eigenvector_centrality,
)

from .flow import (
    edmonds_karp,
    max_flow,
    min_cut,
    ford_fulkerson,
    capacity_scaling,
)

from .matching import (
    hopcroft_karp,
    maximum_bipartite_matching,
    is_perfect_matching,
    maximum_matching,
    matching_size,
    is_maximal_matching,
)

from .coloring import (
    greedy_coloring,
    welsh_powell,
    chromatic_number,
    is_valid_coloring,
    dsatur,
    edge_coloring,
    chromatic_index,
    is_k_colorable,
)

__all__ = [
    # Traversal
    'dfs',
    'dfs_recursive',
    'dfs_iterative',
    'bfs',
    'bfs_levels',
    'topological_sort',
    'topological_sort_dfs',
    'has_cycle',
    'find_path',
    'find_all_paths',
    # Shortest Path
    'dijkstra',
    'bellman_ford',
    'floyd_warshall',
    'a_star',
    'shortest_path',
    'shortest_path_length',
    'all_shortest_paths',
    'reconstruct_path',
    # Connectivity
    'connected_components',
    'is_connected',
    'strongly_connected_components',
    'is_strongly_connected',
    'is_bipartite',
    'find_bridges',
    'find_articulation_points',
    'is_tree',
    'diameter',
    # Spanning Tree
    'kruskal',
    'prim',
    'minimum_spanning_tree',
    'total_weight',
    'is_spanning_tree',
    # Centrality
    'pagerank',
    'betweenness_centrality',
    'closeness_centrality',
    'degree_centrality',
    'eigenvector_centrality',
    # Flow
    'edmonds_karp',
    'max_flow',
    'min_cut',
    'ford_fulkerson',
    'capacity_scaling',
    # Matching
    'hopcroft_karp',
    'maximum_bipartite_matching',
    'is_perfect_matching',
    'maximum_matching',
    'matching_size',
    'is_maximal_matching',
    # Coloring
    'greedy_coloring',
    'welsh_powell',
    'chromatic_number',
    'is_valid_coloring',
    'dsatur',
    'edge_coloring',
    'chromatic_index',
    'is_k_colorable',
]
