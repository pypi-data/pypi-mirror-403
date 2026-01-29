"""
Graph serialization to/from JSON format.

Provides functions to save and load graphs in JSON format.
"""

import json
from typing import Dict, Any
from pathlib import Path
from .graph import Graph
from .vertex import Vertex
from .edge import Edge


def graph_to_json(graph: Graph) -> str:
    """
    Serialize graph to JSON string.

    Args:
        graph: Graph to serialize

    Returns:
        JSON string representation

    Example:
        >>> g = Graph({Vertex('A', attrs={'val': 1})}, {Edge('A', 'B')})
        >>> json_str = graph_to_json(g)
        >>> g2 = graph_from_json(json_str)
    """
    data = {
        'vertices': [
            {
                'id': v.id,
                'attrs': v.attrs
            }
            for v in graph.vertices
        ],
        'edges': [
            {
                'source': e.source,
                'target': e.target,
                'directed': e.directed,
                'weight': e.weight,
                'attrs': e.attrs
            }
            for e in graph.edges
        ]
    }
    return json.dumps(data, indent=2)


def graph_from_json(json_str: str) -> Graph:
    """
    Deserialize graph from JSON string.

    Args:
        json_str: JSON string representation

    Returns:
        Graph object

    Example:
        >>> json_str = '{"vertices": [{"id": "A", "attrs": {}}], "edges": []}'
        >>> g = graph_from_json(json_str)
        >>> g.has_vertex('A')
        True
    """
    data = json.loads(json_str)

    # Reconstruct vertices
    vertices = {
        Vertex(v['id'], attrs=v.get('attrs', {}))
        for v in data.get('vertices', [])
    }

    # Reconstruct edges
    edges = {
        Edge(
            e['source'],
            e['target'],
            directed=e.get('directed', True),
            weight=e.get('weight', 1.0),
            attrs=e.get('attrs', {})
        )
        for e in data.get('edges', [])
    }

    return Graph(vertices, edges)


def save_graph(graph: Graph, filepath: str) -> None:
    """
    Save graph to JSON file.

    Args:
        graph: Graph to save
        filepath: Path to output file

    Example:
        >>> g = Graph({Vertex('A')}, {Edge('A', 'B')})
        >>> save_graph(g, 'my_graph.json')
    """
    json_str = graph_to_json(graph)
    Path(filepath).write_text(json_str)


def load_graph(filepath: str) -> Graph:
    """
    Load graph from JSON file.

    Args:
        filepath: Path to input file

    Returns:
        Graph object

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON

    Example:
        >>> g = load_graph('my_graph.json')
        >>> print(g.vertex_count)
    """
    json_str = Path(filepath).read_text()
    return graph_from_json(json_str)


__all__ = [
    'graph_to_json',
    'graph_from_json',
    'save_graph',
    'load_graph',
]
