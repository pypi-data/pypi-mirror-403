"""
Interoperability between AlgoTree and AlgoGraph.

Provides conversion functions between tree and graph representations.
Trees are special cases of graphs (acyclic, connected, directed from parent to child).

Note: AlgoTree must be installed or in PYTHONPATH for interop functions to work.
"""

from typing import Set, Dict, Optional, Any

try:
    from AlgoTree.node import Node
    from AlgoTree.tree import Tree
    ALGOTREE_AVAILABLE = True
except ImportError:
    ALGOTREE_AVAILABLE = False
    Node = None
    Tree = None

from .vertex import Vertex
from .edge import Edge
from .graph import Graph


def _require_algotree():
    """Check if AlgoTree is available."""
    if not ALGOTREE_AVAILABLE:
        raise ImportError(
            "AlgoTree is required for interop functions. "
            "Install AlgoTree or add it to PYTHONPATH."
        )


def tree_to_graph(tree, directed: bool = True) -> Graph:
    """
    Convert AlgoTree Tree to AlgoGraph Graph.

    Each tree node becomes a graph vertex.
    Parent-child relationships become directed edges.

    Args:
        tree: AlgoTree Tree to convert
        directed: Whether edges should be directed (default: True)

    Returns:
        AlgoGraph Graph representation

    Example:
        >>> from AlgoTree import Node, Tree
        >>> tree = Tree(Node('root', Node('child1'), Node('child2')))
        >>> graph = tree_to_graph(tree)
        >>> graph.vertex_count
        3
        >>> graph.edge_count
        2
    """
    _require_algotree()
    vertices = set()
    edges = set()

    def traverse(node: Node, parent_id: Optional[str] = None):
        # Create vertex from node
        vertex = Vertex(node.name, attrs=node.attrs.copy())
        vertices.add(vertex)

        # Create edge from parent
        if parent_id is not None:
            edge = Edge(parent_id, node.name, directed=directed, weight=1.0)
            edges.add(edge)

        # Recurse to children
        for child in node.children:
            traverse(child, node.name)

    traverse(tree.root)
    return Graph(vertices=vertices, edges=edges)


def node_to_graph(node: Node, directed: bool = True) -> Graph:
    """
    Convert AlgoTree Node (and its subtree) to AlgoGraph Graph.

    Args:
        node: Root node of tree
        directed: Whether edges should be directed

    Returns:
        AlgoGraph Graph representation

    Example:
        >>> from AlgoTree import Node
        >>> node = Node('A', Node('B'), Node('C'))
        >>> graph = node_to_graph(node)
        >>> graph.has_vertex('A')
        True
    """
    tree = Tree(node)
    return tree_to_graph(tree, directed=directed)


def graph_to_tree(graph: Graph, root_id: str) -> Tree:
    """
    Convert AlgoGraph Graph to AlgoTree Tree.

    Extracts a spanning tree from the graph starting at root_id.
    Uses BFS traversal to build the tree.

    Args:
        graph: AlgoGraph Graph to convert
        root_id: Vertex ID to use as tree root

    Returns:
        AlgoTree Tree representation

    Raises:
        ValueError: If root_id not in graph or graph has cycles

    Example:
        >>> v1, v2, v3 = Vertex('A'), Vertex('B'), Vertex('C')
        >>> e1, e2 = Edge('A', 'B'), Edge('A', 'C')
        >>> graph = Graph({v1, v2, v3}, {e1, e2})
        >>> tree = graph_to_tree(graph, 'A')
        >>> tree.root.name
        'A'
    """
    if not graph.has_vertex(root_id):
        raise ValueError(f"Root vertex '{root_id}' not in graph")

    from collections import deque

    # BFS to build tree
    visited = set()
    queue = deque([root_id])
    parent_map = {root_id: None}

    while queue:
        current_id = queue.popleft()

        if current_id in visited:
            continue

        visited.add(current_id)

        # Add unvisited neighbors
        for neighbor_id in graph.neighbors(current_id):
            if neighbor_id not in visited:
                parent_map[neighbor_id] = current_id
                queue.append(neighbor_id)

    # Build tree from parent map
    def build_node(vertex_id: str) -> Node:
        vertex = graph.get_vertex(vertex_id)
        if vertex is None:
            vertex = Vertex(vertex_id)

        # Find children (nodes whose parent is this vertex)
        children = []
        for vid, parent_id in parent_map.items():
            if parent_id == vertex_id:
                children.append(build_node(vid))

        return Node(vertex.id, *children, attrs=vertex.attrs.copy())

    root_node = build_node(root_id)
    return Tree(root_node)


def flat_dict_to_graph(flat_dict: Dict[str, Any], directed: bool = True) -> Graph:
    """
    Convert flat dictionary format to Graph.

    The flat format (from AlgoTree exporters) uses:
    - Keys: vertex IDs
    - Values: dicts with .name, .children (or .edges), and attributes

    Args:
        flat_dict: Flat dictionary representation
        directed: Whether edges should be directed

    Returns:
        AlgoGraph Graph

    Example:
        >>> flat = {
        ...     'A': {'.name': 'A', '.children': ['B', 'C'], 'value': 10},
        ...     'B': {'.name': 'B', '.children': [], 'value': 20},
        ...     'C': {'.name': 'C', '.children': [], 'value': 30}
        ... }
        >>> graph = flat_dict_to_graph(flat)
        >>> graph.vertex_count
        3
    """
    vertices = set()
    edges = set()

    for vertex_id, data in flat_dict.items():
        # Extract metadata
        name = data.get('.name', vertex_id)

        # Extract regular attributes (non-dot-prefixed)
        attrs = {k: v for k, v in data.items() if not k.startswith('.')}

        # Create vertex
        vertex = Vertex(name, attrs=attrs)
        vertices.add(vertex)

        # Create edges from .children or .edges
        children = data.get('.children', data.get('.edges', []))
        for child_id in children:
            weight = 1.0
            # Check if child is a dict with weight
            if isinstance(child_id, dict):
                weight = child_id.get('weight', 1.0)
                child_id = child_id.get('target', child_id.get('id'))

            edge = Edge(name, child_id, directed=directed, weight=weight)
            edges.add(edge)

    return Graph(vertices=vertices, edges=edges)


def graph_to_flat_dict(graph: Graph) -> Dict[str, Any]:
    """
    Convert Graph to flat dictionary format.

    Compatible with AlgoTree's flat export format.

    Args:
        graph: AlgoGraph Graph

    Returns:
        Flat dictionary representation

    Example:
        >>> g = Graph({Vertex('A'), Vertex('B')}, {Edge('A', 'B')})
        >>> flat = graph_to_flat_dict(g)
        >>> 'A' in flat
        True
        >>> flat['A']['.edges']
        [{'target': 'B', 'weight': 1.0, 'directed': True}]
    """
    flat_dict = {}

    for vertex in graph.vertices:
        # Build vertex entry
        entry = {
            '.name': vertex.id,
            '.edges': []
        }

        # Add attributes
        entry.update(vertex.attrs)

        # Add edges
        for edge in graph.edges:
            if edge.source == vertex.id:
                edge_data = {
                    'target': edge.target,
                    'weight': edge.weight,
                    'directed': edge.directed
                }
                # Add edge attributes
                if edge.attrs:
                    edge_data.update(edge.attrs)

                entry['.edges'].append(edge_data)

        flat_dict[vertex.id] = entry

    return flat_dict


# Convenience functions
def tree_to_flat_dict(tree: Tree) -> Dict[str, Any]:
    """Convert Tree to flat dict via Graph."""
    graph = tree_to_graph(tree)
    return graph_to_flat_dict(graph)


def flat_dict_to_tree(flat_dict: Dict[str, Any], root_id: str) -> Tree:
    """Convert flat dict to Tree via Graph."""
    graph = flat_dict_to_graph(flat_dict)
    return graph_to_tree(graph, root_id)
