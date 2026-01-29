"""
Visualization export for AlgoGraph.

Provides export to various visualization formats:
- GraphViz DOT format for rendering with graphviz tools
- D3.js JSON format for web-based visualization
- Mermaid flowchart format for documentation

Example usage:
    >>> from AlgoGraph.visualization import to_dot, to_d3_json, to_mermaid
    >>>
    >>> # Export to DOT format
    >>> dot_string = to_dot(graph)
    >>> with open('graph.dot', 'w') as f:
    ...     f.write(dot_string)
    >>>
    >>> # Export to D3.js JSON
    >>> d3_data = to_d3_json(graph)
    >>> import json
    >>> with open('graph.json', 'w') as f:
    ...     json.dump(d3_data, f)
    >>>
    >>> # Export to Mermaid
    >>> mermaid = to_mermaid(graph)
    >>> print(mermaid)
"""

import json
from typing import Any, Callable, Dict, List, Optional, Set, Union

from .graph import Graph
from .vertex import Vertex
from .edge import Edge


def to_dot(
    graph: Graph,
    name: str = "G",
    directed: bool = True,
    node_attrs: Optional[Callable[[Vertex], Dict[str, str]]] = None,
    edge_attrs: Optional[Callable[[Edge], Dict[str, str]]] = None,
    graph_attrs: Optional[Dict[str, str]] = None,
    rankdir: Optional[str] = None,
    include_weights: bool = True,
) -> str:
    """
    Export graph to GraphViz DOT format.

    Args:
        graph: The graph to export
        name: Name of the graph
        directed: True for digraph, False for graph
        node_attrs: Function to generate node attributes from vertex
        edge_attrs: Function to generate edge attributes from edge
        graph_attrs: Graph-level attributes
        rankdir: Graph direction (TB, BT, LR, RL)
        include_weights: Include edge weights as labels

    Returns:
        DOT format string

    Example:
        >>> dot = to_dot(graph, name="MyGraph", rankdir="LR")
        >>> print(dot)
        digraph MyGraph {
            rankdir=LR;
            A [label="A"];
            B [label="B"];
            A -> B [weight=1.0, label="1.0"];
        }
    """
    graph_type = "digraph" if directed else "graph"
    edge_op = "->" if directed else "--"

    lines = [f'{graph_type} {_escape_id(name)} {{']

    # Graph attributes
    if graph_attrs:
        for key, value in graph_attrs.items():
            lines.append(f'    {key}={_quote_attr(value)};')

    if rankdir:
        lines.append(f'    rankdir={rankdir};')

    # Node definitions
    for vertex in sorted(graph.vertices, key=lambda v: v.id):
        attrs = {"label": vertex.id}

        # Add custom node attributes
        if node_attrs:
            attrs.update(node_attrs(vertex))
        else:
            # Default: include vertex attributes
            for key, value in vertex.attrs.items():
                if key not in attrs:
                    attrs[key] = str(value)

        attr_str = _format_attrs(attrs)
        lines.append(f'    {_escape_id(vertex.id)} [{attr_str}];')

    # Edge definitions
    for edge in sorted(graph.edges, key=lambda e: (e.source, e.target)):
        attrs = {}

        if include_weights and edge.weight != 1.0:
            attrs["weight"] = str(edge.weight)
            attrs["label"] = str(edge.weight)

        # Add custom edge attributes
        if edge_attrs:
            attrs.update(edge_attrs(edge))
        else:
            # Default: include edge attributes
            for key, value in edge.attrs.items():
                if key not in attrs:
                    attrs[key] = str(value)

        attr_str = _format_attrs(attrs) if attrs else ""
        if attr_str:
            lines.append(
                f'    {_escape_id(edge.source)} {edge_op} '
                f'{_escape_id(edge.target)} [{attr_str}];'
            )
        else:
            lines.append(
                f'    {_escape_id(edge.source)} {edge_op} '
                f'{_escape_id(edge.target)};'
            )

    lines.append('}')
    return '\n'.join(lines)


def to_d3_json(
    graph: Graph,
    node_attrs: Optional[Callable[[Vertex], Dict[str, Any]]] = None,
    link_attrs: Optional[Callable[[Edge], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Export graph to D3.js force-directed graph JSON format.

    The format is compatible with D3.js force simulation:
    {
        "nodes": [{"id": "A", "group": 1, ...}, ...],
        "links": [{"source": "A", "target": "B", "value": 1.0, ...}, ...]
    }

    Args:
        graph: The graph to export
        node_attrs: Function to add custom node attributes
        link_attrs: Function to add custom link attributes

    Returns:
        Dictionary in D3.js format

    Example:
        >>> data = to_d3_json(graph)
        >>> import json
        >>> print(json.dumps(data, indent=2))
    """
    # Build node list
    nodes = []
    vertex_index = {}

    for i, vertex in enumerate(sorted(graph.vertices, key=lambda v: v.id)):
        vertex_index[vertex.id] = i
        node = {"id": vertex.id}

        # Add vertex attributes
        for key, value in vertex.attrs.items():
            node[key] = value

        # Add custom attributes
        if node_attrs:
            node.update(node_attrs(vertex))

        nodes.append(node)

    # Build link list
    links = []
    for edge in sorted(graph.edges, key=lambda e: (e.source, e.target)):
        link = {
            "source": edge.source,
            "target": edge.target,
            "value": edge.weight,
        }

        # Add edge attributes
        for key, value in edge.attrs.items():
            link[key] = value

        # Add custom attributes
        if link_attrs:
            link.update(link_attrs(edge))

        links.append(link)

    return {"nodes": nodes, "links": links}


def to_d3_hierarchical(
    graph: Graph,
    root: str,
    node_attrs: Optional[Callable[[Vertex], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Export graph to D3.js hierarchical JSON format (tree layout).

    Creates a nested structure suitable for D3's tree/cluster layouts.
    Only follows outgoing edges from each node.

    Args:
        graph: The graph to export
        root: ID of the root vertex
        node_attrs: Function to add custom node attributes

    Returns:
        Nested dictionary for hierarchical visualization

    Example:
        >>> data = to_d3_hierarchical(graph, root='A')
        >>> # {"name": "A", "children": [{"name": "B", ...}, ...]}
    """
    def build_tree(vertex_id: str, visited: Set[str]) -> Dict[str, Any]:
        if vertex_id in visited:
            return {"name": vertex_id, "children": []}

        visited.add(vertex_id)

        vertex = graph.get_vertex(vertex_id)
        node = {"name": vertex_id}

        if vertex:
            for key, value in vertex.attrs.items():
                node[key] = value

            if node_attrs:
                node.update(node_attrs(vertex))

        # Get children (outgoing edges)
        children = []
        for neighbor_id in graph.neighbors(vertex_id):
            child = build_tree(neighbor_id, visited.copy())
            children.append(child)

        if children:
            node["children"] = children

        return node

    return build_tree(root, set())


def to_mermaid(
    graph: Graph,
    direction: str = "TD",
    include_weights: bool = True,
    node_shape: str = "rect",
) -> str:
    """
    Export graph to Mermaid flowchart format.

    Mermaid is useful for embedding diagrams in Markdown documentation.

    Args:
        graph: The graph to export
        direction: Flow direction (TD=top-down, LR=left-right, BT, RL)
        include_weights: Include edge weights as labels
        node_shape: Node shape (rect, round, stadium, circle, diamond)

    Returns:
        Mermaid flowchart string

    Example:
        >>> mermaid = to_mermaid(graph, direction="LR")
        >>> print(mermaid)
        flowchart LR
            A[A]
            B[B]
            A -->|1.0| B
    """
    lines = [f"flowchart {direction}"]

    # Shape brackets
    shapes = {
        "rect": ("[", "]"),
        "round": ("(", ")"),
        "stadium": ("([", "])"),
        "circle": ("((", "))"),
        "diamond": ("{", "}"),
    }
    left, right = shapes.get(node_shape, ("[", "]"))

    # Node definitions
    for vertex in sorted(graph.vertices, key=lambda v: v.id):
        node_id = _mermaid_id(vertex.id)
        label = vertex.id
        lines.append(f"    {node_id}{left}{label}{right}")

    # Edge definitions
    for edge in sorted(graph.edges, key=lambda e: (e.source, e.target)):
        source = _mermaid_id(edge.source)
        target = _mermaid_id(edge.target)

        if include_weights and edge.weight != 1.0:
            lines.append(f"    {source} -->|{edge.weight}| {target}")
        else:
            lines.append(f"    {source} --> {target}")

    return '\n'.join(lines)


def to_adjacency_json(graph: Graph) -> Dict[str, Any]:
    """
    Export graph to adjacency list JSON format.

    Creates a simple format mapping each vertex to its neighbors:
    {
        "vertices": {"A": {"attrs": {...}}, ...},
        "adjacency": {"A": ["B", "C"], ...}
    }

    Args:
        graph: The graph to export

    Returns:
        Dictionary with vertices and adjacency lists
    """
    vertices = {}
    for vertex in graph.vertices:
        vertices[vertex.id] = {"attrs": vertex.attrs}

    adjacency = {}
    for vertex in graph.vertices:
        adjacency[vertex.id] = list(graph.neighbors(vertex.id))

    return {"vertices": vertices, "adjacency": adjacency}


def to_cytoscape_json(
    graph: Graph,
    node_attrs: Optional[Callable[[Vertex], Dict[str, Any]]] = None,
    edge_attrs: Optional[Callable[[Edge], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Export graph to Cytoscape.js JSON format.

    Cytoscape.js is a popular graph visualization library.

    Args:
        graph: The graph to export
        node_attrs: Function to add custom node data
        edge_attrs: Function to add custom edge data

    Returns:
        Dictionary in Cytoscape.js format

    Example:
        >>> data = to_cytoscape_json(graph)
        >>> # {"elements": {"nodes": [...], "edges": [...]}}
    """
    nodes = []
    for vertex in graph.vertices:
        data = {"id": vertex.id}
        data.update(vertex.attrs)
        if node_attrs:
            data.update(node_attrs(vertex))
        nodes.append({"data": data})

    edges = []
    for i, edge in enumerate(graph.edges):
        data = {
            "id": f"e{i}",
            "source": edge.source,
            "target": edge.target,
            "weight": edge.weight,
        }
        data.update(edge.attrs)
        if edge_attrs:
            data.update(edge_attrs(edge))
        edges.append({"data": data})

    return {"elements": {"nodes": nodes, "edges": edges}}


def to_sigma_json(
    graph: Graph,
    node_attrs: Optional[Callable[[Vertex], Dict[str, Any]]] = None,
    edge_attrs: Optional[Callable[[Edge], Dict[str, Any]]] = None,
    layout: Optional[Dict[str, Dict[str, float]]] = None,
) -> Dict[str, Any]:
    """
    Export graph to Sigma.js JSON format.

    Sigma.js is a lightweight graph drawing library.

    Args:
        graph: The graph to export
        node_attrs: Function to add custom node data
        edge_attrs: Function to add custom edge data
        layout: Pre-computed positions {vertex_id: {"x": float, "y": float}}

    Returns:
        Dictionary in Sigma.js format
    """
    import math

    nodes = []
    for i, vertex in enumerate(sorted(graph.vertices, key=lambda v: v.id)):
        # Default circular layout if no positions provided
        if layout and vertex.id in layout:
            x = layout[vertex.id].get("x", 0)
            y = layout[vertex.id].get("y", 0)
        else:
            angle = (2 * math.pi * i) / max(graph.vertex_count, 1)
            x = math.cos(angle) * 100
            y = math.sin(angle) * 100

        node = {
            "id": vertex.id,
            "label": vertex.id,
            "x": x,
            "y": y,
            "size": 1,
        }
        node.update(vertex.attrs)
        if node_attrs:
            node.update(node_attrs(vertex))
        nodes.append(node)

    edges = []
    for i, edge in enumerate(graph.edges):
        e = {
            "id": f"e{i}",
            "source": edge.source,
            "target": edge.target,
            "weight": edge.weight,
        }
        e.update(edge.attrs)
        if edge_attrs:
            e.update(edge_attrs(edge))
        edges.append(e)

    return {"nodes": nodes, "edges": edges}


# Helper functions

def _escape_id(s: str) -> str:
    """Escape a string for use as a DOT identifier."""
    # If it's a simple identifier, return as-is
    if s.isalnum() or (s.replace('_', '').isalnum() and not s[0].isdigit()):
        return s
    # Otherwise, quote it
    return f'"{s}"'


def _quote_attr(value: str) -> str:
    """Quote an attribute value for DOT format."""
    if value.replace('_', '').replace('-', '').isalnum():
        return value
    # Escape quotes and wrap
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'


def _format_attrs(attrs: Dict[str, str]) -> str:
    """Format attributes for DOT format."""
    parts = []
    for key, value in attrs.items():
        parts.append(f'{key}={_quote_attr(value)}')
    return ', '.join(parts)


def _mermaid_id(s: str) -> str:
    """Convert a string to a valid Mermaid node ID."""
    # Replace spaces and special chars with underscores
    result = ""
    for c in s:
        if c.isalnum():
            result += c
        else:
            result += "_"
    return result or "node"


# Convenience functions for saving to files

def save_dot(graph: Graph, filepath: str, **kwargs) -> None:
    """
    Save graph to a DOT file.

    Args:
        graph: The graph to export
        filepath: Path to output file
        **kwargs: Additional arguments for to_dot()
    """
    dot = to_dot(graph, **kwargs)
    with open(filepath, 'w') as f:
        f.write(dot)


def save_d3_json(graph: Graph, filepath: str, **kwargs) -> None:
    """
    Save graph to a D3.js JSON file.

    Args:
        graph: The graph to export
        filepath: Path to output file
        **kwargs: Additional arguments for to_d3_json()
    """
    data = to_d3_json(graph, **kwargs)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def save_mermaid(graph: Graph, filepath: str, **kwargs) -> None:
    """
    Save graph to a Mermaid file.

    Args:
        graph: The graph to export
        filepath: Path to output file
        **kwargs: Additional arguments for to_mermaid()
    """
    mermaid = to_mermaid(graph, **kwargs)
    with open(filepath, 'w') as f:
        f.write(mermaid)
