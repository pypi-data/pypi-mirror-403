"""
AlgoGraph - Graph Data Structures and Algorithms

A modern, immutable graph library with elegant functional APIs.
Provides transformers, selectors, and lazy views for productive graph programming.

Core Components:
- Vertex: Immutable graph vertices with attributes
- Edge: Immutable directed/undirected edges with weights
- Graph: Immutable graph container with 56+ algorithms
- GraphBuilder: Fluent API for graph construction

Advanced Features (v2.0.0):
- Transformers: Composable transformations with | pipe operator
- Selectors: Declarative queries with logical operators
- Views: Lazy evaluation for efficient filtering

Example:
    >>> from AlgoGraph import Vertex, Edge, Graph
    >>> v1, v2 = Vertex('A'), Vertex('B')
    >>> e = Edge('A', 'B', weight=5.0)
    >>> g = Graph({v1, v2}, {e})
    >>> g.has_edge('A', 'B')
    True

Transformer Pipeline:
    >>> from AlgoGraph.transformers import filter_vertices, to_dict
    >>> result = graph | filter_vertices(lambda v: v.get('active')) | to_dict()

Declarative Selectors:
    >>> from AlgoGraph.graph_selectors import vertex as v
    >>> matches = graph.select_vertices(v.attrs(age=lambda a: a > 30) & v.degree(min_degree=5))

Lazy Views:
    >>> from AlgoGraph.views import filtered_view
    >>> view = filtered_view(large_graph, vertex_filter=lambda v: v.get('active'))
    >>> small_graph = view.materialize()  # Lazy, no copying until now

Integration with AlgoTree:
    >>> from AlgoTree import Node, Tree
    >>> from AlgoGraph import tree_to_graph, graph_to_tree
    >>> tree = Tree(Node('root', Node('child1'), Node('child2')))
    >>> graph = tree_to_graph(tree)
    >>> recovered_tree = graph_to_tree(graph, 'root')
"""

from .vertex import Vertex
from .edge import Edge
from .graph import Graph
from .builder import GraphBuilder
from .interop import (
    tree_to_graph,
    node_to_graph,
    graph_to_tree,
    flat_dict_to_graph,
    graph_to_flat_dict,
    tree_to_flat_dict,
    flat_dict_to_tree,
)
from .serialization import (
    graph_to_json,
    graph_from_json,
    save_graph,
    load_graph,
)

# Algorithms are available in submodule
# from AlgoGraph.algorithms import dfs, bfs, dijkstra, etc.

# Transformers, selectors, and views are available in submodules
# from AlgoGraph.transformers import filter_vertices, map_vertices, etc.
# from AlgoGraph.graph_selectors import vertex, edge
# from AlgoGraph.views import filtered_view, subgraph_view, etc.

__version__ = "2.0.0"

__all__ = [
    'Vertex',
    'Edge',
    'Graph',
    'GraphBuilder',
    'tree_to_graph',
    'node_to_graph',
    'graph_to_tree',
    'flat_dict_to_graph',
    'graph_to_flat_dict',
    'tree_to_flat_dict',
    'flat_dict_to_tree',
    'graph_to_json',
    'graph_from_json',
    'save_graph',
    'load_graph',
]
