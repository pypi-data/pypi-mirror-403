# AlgoGraph

Immutable graph data structures and algorithms library with functional transformers, declarative selectors, and lazy views.

[![PyPI version](https://badge.fury.io/py/AlgoGraph.svg)](https://pypi.org/project/AlgoGraph/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install AlgoGraph
```

## Overview

AlgoGraph provides immutable graph data structures with a clean, functional API. Version 2.0.0 brings AlgoTree-level API elegance with pipe-based transformers, declarative selectors, and lazy views—achieving ~90% code reduction for common operations.

## Key Features

- **Immutable by default**: All operations return new graph objects
- **56+ algorithms**: Traversal, shortest path, centrality, flow, matching, coloring
- **Pipe-based transformers**: Composable operations with `|` operator (v2.0.0)
- **Declarative selectors**: Pattern matching with logical operators (v2.0.0)
- **Lazy views**: Memory-efficient filtering without copying (v2.0.0)
- **Fluent builder API**: Construct graphs with 82% less code
- **Type-safe**: Full type hints for IDE support
- **Optional AlgoTree integration**: Convert between trees and graphs

## Quick Start

```python
from AlgoGraph import Graph, Vertex, Edge

# Create a graph
g = (Graph.builder()
     .add_vertex('A', age=30)
     .add_vertex('B', age=25)
     .add_edge('A', 'B', weight=5.0)
     .build())

# Query the graph
g.has_edge('A', 'B')  # True
g.neighbors('A')       # {'B'}

# Run algorithms
from AlgoGraph.algorithms import dijkstra, pagerank
distances = dijkstra(g, source='A')
```

## Advanced Features (v2.0.0)

### Transformer Pipelines

Compose graph operations using the `|` pipe operator:

```python
from AlgoGraph.transformers import filter_vertices, largest_component, stats

# Filter → extract component → compute stats
result = (graph
    | filter_vertices(lambda v: v.get('active'))
    | largest_component()
    | stats())

# result: {'vertex_count': 42, 'edge_count': 156, 'density': 0.18, ...}
```

**Available Transformers:**
- `filter_vertices(pred)`, `filter_edges(pred)` - Filter by predicate
- `map_vertices(fn)`, `map_edges(fn)` - Transform attributes
- `reverse()`, `to_undirected()` - Structure transformations
- `largest_component()`, `minimum_spanning_tree()` - Algorithm-based
- `to_dict()`, `to_adjacency_list()`, `stats()` - Export operations

### Declarative Selectors

Query vertices and edges with logical operators:

```python
from AlgoGraph.graph_selectors import vertex as v, edge as e

# Find active users with high degree
power_users = graph.select_vertices(
    v.attrs(active=True) & v.degree(min_degree=10)
)

# Find heavy edges from admin nodes
admin_edges = graph.select_edges(
    e.source(v.attrs(role='admin')) & e.weight(min_weight=100)
)

# Complex queries with OR, NOT, XOR
special = graph.select_vertices(
    (v.attrs(vip=True) | v.degree(min_degree=50)) & ~v.attrs(banned=True)
)
```

**Selector Types:**
- `vertex.id(pattern)` - Match by ID (glob/regex)
- `vertex.attrs(**attrs)` - Match attributes (supports callables)
- `vertex.degree(min/max/exact)` - Match by degree
- `edge.weight(min/max/exact)` - Match by weight
- `edge.source(selector)`, `edge.target(selector)` - Match endpoints

### Lazy Views

Efficient filtering without copying data:

```python
from AlgoGraph.views import filtered_view, neighborhood_view

# Create view without copying
view = filtered_view(
    large_graph,
    vertex_filter=lambda v: v.get('active'),
    edge_filter=lambda e: e.weight > 5.0
)

# Iterate lazily
for vertex in view.vertices():
    process(vertex)

# Materialize only when needed
small_graph = view.materialize()

# Explore k-hop neighborhood
local = neighborhood_view(graph, center='Alice', k=2)
```

**View Types:**
- `filtered_view()` - Filter vertices/edges
- `subgraph_view()` - View specific vertices
- `reversed_view()` - Reverse edge directions
- `undirected_view()` - View as undirected
- `neighborhood_view()` - k-hop neighborhood

## Core Classes

### Vertex

```python
from AlgoGraph import Vertex

v = Vertex('A', attrs={'value': 10, 'color': 'red'})
v2 = v.with_attrs(value=20)      # Immutable update
v3 = v.without_attrs('color')    # Remove attribute
```

### Edge

```python
from AlgoGraph import Edge

e = Edge('A', 'B', directed=True, weight=5.0)
e2 = e.with_weight(10.0)  # Immutable update
e3 = e.reversed()         # B -> A
```

### Graph

```python
from AlgoGraph import Graph, Vertex, Edge

# Direct construction
g = Graph({Vertex('A'), Vertex('B')}, {Edge('A', 'B')})

# Fluent builder
g = (Graph.builder()
     .add_vertex('A', age=30)
     .add_edge('A', 'B', weight=5.0)
     .add_path('B', 'C', 'D')
     .add_cycle('X', 'Y', 'Z')
     .build())

# From edges (auto-creates vertices)
g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'A'))

# Immutable operations
g2 = g.add_vertex(Vertex('D'))
g3 = g.remove_vertex('A')
g4 = g.subgraph({'B', 'C', 'D'})
```

## Algorithms

### Traversal

```python
from AlgoGraph.algorithms import dfs, bfs, topological_sort, has_cycle, find_path

visited = dfs(graph, start_vertex='A')
levels = bfs(graph, start_vertex='A')
order = topological_sort(graph)  # DAG only
path = find_path(graph, 'A', 'Z')
```

### Shortest Paths

```python
from AlgoGraph.algorithms import dijkstra, bellman_ford, floyd_warshall, a_star

distances = dijkstra(graph, source='A')
distances = bellman_ford(graph, source='A')  # Handles negative weights
all_pairs = floyd_warshall(graph)
path = a_star(graph, 'A', 'Z', heuristic=h)
```

### Connectivity

```python
from AlgoGraph.algorithms import (
    connected_components, strongly_connected_components,
    is_connected, is_bipartite, find_bridges, find_articulation_points
)

components = connected_components(graph)
scc = strongly_connected_components(graph)
bridges = find_bridges(graph)
articulation = find_articulation_points(graph)
```

### Spanning Trees

```python
from AlgoGraph.algorithms import minimum_spanning_tree, kruskal, prim

mst = minimum_spanning_tree(graph)
mst = kruskal(graph)
mst = prim(graph, start='A')
```

### Centrality

```python
from AlgoGraph.algorithms import (
    pagerank, betweenness_centrality, closeness_centrality,
    degree_centrality, eigenvector_centrality
)

pr = pagerank(social_network)
bc = betweenness_centrality(network)
cc = closeness_centrality(network)
```

### Flow Networks

```python
from AlgoGraph.algorithms import max_flow, min_cut, edmonds_karp

flow_value = max_flow(network, 'Source', 'Sink')
cut_value, source_set, sink_set = min_cut(network, 'Source', 'Sink')
```

### Matching

```python
from AlgoGraph.algorithms import hopcroft_karp, maximum_bipartite_matching, is_perfect_matching

matching = hopcroft_karp(bipartite_graph, left_set, right_set)
max_matching = maximum_bipartite_matching(graph, left, right)
```

### Graph Coloring

```python
from AlgoGraph.algorithms import welsh_powell, chromatic_number, dsatur, is_k_colorable

coloring = welsh_powell(graph)
num_colors = chromatic_number(graph)
coloring = dsatur(graph)  # Often better than greedy
```

## Serialization

```python
from AlgoGraph import save_graph, load_graph

# Save/load JSON
save_graph(graph, 'network.json')
graph = load_graph('network.json')
```

## AlgoTree Integration (Optional)

```python
from AlgoTree import Node, Tree
from AlgoGraph import tree_to_graph, graph_to_tree

# Tree to Graph
tree = Tree(Node('root', Node('child1'), Node('child2')))
graph = tree_to_graph(tree)

# Graph to Tree (extracts spanning tree)
tree = graph_to_tree(graph, root='root')
```

## Interactive Shell

Explore graphs with a filesystem-like interface:

```bash
pip install AlgoGraph
algograph                    # Start with sample graph
algograph network.json       # Load from file
```

```
graph(5v):/$ ls
Alice/  [2 neighbors]
Bob/    [3 neighbors]

graph(5v):/$ cd Alice
graph(5v):/Alice$ ls
Attributes:
  age = 30
neighbors/  [2 vertices]

graph(5v):/Alice$ path Bob Eve
Path found: Alice -> Bob -> Diana -> Eve
```

## Examples

### Social Network Analysis

```python
from AlgoGraph import Graph
from AlgoGraph.algorithms import pagerank, betweenness_centrality
from AlgoGraph.transformers import filter_vertices, stats
from AlgoGraph.graph_selectors import vertex as v

# Build network
network = (Graph.builder()
    .add_vertex('Alice', followers=1000)
    .add_vertex('Bob', followers=500)
    .add_vertex('Charlie', followers=2000)
    .add_edge('Alice', 'Bob', directed=False)
    .add_edge('Bob', 'Charlie', directed=False)
    .add_edge('Alice', 'Charlie', directed=False)
    .build())

# Find influencers
pr = pagerank(network)
top_influencer = max(pr, key=pr.get)

# Find power users with selector
power_users = network.select_vertices(
    v.attrs(followers=lambda f: f > 800)
)

# Analyze active subgraph
analysis = (network
    | filter_vertices(lambda v: v.get('followers', 0) > 500)
    | stats())
```

### Road Network

```python
from AlgoGraph import Graph
from AlgoGraph.algorithms import dijkstra, minimum_spanning_tree

roads = (Graph.builder()
    .add_edge('NYC', 'Boston', weight=215, directed=False)
    .add_edge('NYC', 'DC', weight=225, directed=False)
    .add_edge('Boston', 'DC', weight=440, directed=False)
    .build())

# Shortest routes from NYC
distances = dijkstra(roads, 'NYC')

# Minimum cost network
mst = minimum_spanning_tree(roads)
```

## Design Philosophy

1. **Immutability**: All operations return new objects
2. **Composability**: Chain operations with `|` pipe operator
3. **Declarative**: Express *what*, not *how* (selectors vs lambdas)
4. **Lazy evaluation**: Views defer computation until needed
5. **Type safety**: Full type hints throughout

## Related Projects

- **[AlgoTree](https://github.com/queelius/AlgoTree)**: Tree data structures and algorithms
- **[NetworkX](https://networkx.org/)**: Comprehensive Python graph library (mutable)
- **[graph-tool](https://graph-tool.skewed.de/)**: High-performance graph analysis

## License

MIT License - see LICENSE file for details.
