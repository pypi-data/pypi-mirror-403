"""
Tests for the visualization export module.
"""

import pytest
import json
import tempfile
import os

from AlgoGraph import Graph, Vertex, Edge
from AlgoGraph.visualization import (
    to_dot, to_d3_json, to_d3_hierarchical, to_mermaid,
    to_adjacency_json, to_cytoscape_json, to_sigma_json,
    save_dot, save_d3_json, save_mermaid
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def simple_graph():
    """Simple test graph: A -> B -> C"""
    return Graph(
        vertices={
            Vertex('A', attrs={'color': 'red', 'size': 10}),
            Vertex('B', attrs={'color': 'blue', 'size': 20}),
            Vertex('C', attrs={'color': 'green', 'size': 30}),
        },
        edges={
            Edge('A', 'B', weight=1.5),
            Edge('B', 'C', weight=2.5),
        }
    )


@pytest.fixture
def tree_graph():
    """Tree-like graph for hierarchical tests."""
    return Graph(
        vertices={
            Vertex('root'),
            Vertex('child1'),
            Vertex('child2'),
            Vertex('grandchild1'),
            Vertex('grandchild2'),
        },
        edges={
            Edge('root', 'child1'),
            Edge('root', 'child2'),
            Edge('child1', 'grandchild1'),
            Edge('child1', 'grandchild2'),
        }
    )


@pytest.fixture
def graph_with_spaces():
    """Graph with spaces in vertex names."""
    return Graph(
        vertices={
            Vertex('Node A', attrs={'label': 'First'}),
            Vertex('Node B', attrs={'label': 'Second'}),
        },
        edges={
            Edge('Node A', 'Node B', weight=1.0),
        }
    )


# ============================================================================
# DOT Format Tests
# ============================================================================

class TestDotExport:
    """Tests for GraphViz DOT export."""

    def test_basic_dot_export(self, simple_graph):
        """Basic DOT export."""
        dot = to_dot(simple_graph)

        assert 'digraph' in dot
        assert 'A' in dot
        assert 'B' in dot
        assert 'C' in dot
        assert '->' in dot

    def test_undirected_graph(self, simple_graph):
        """Export as undirected graph."""
        dot = to_dot(simple_graph, directed=False)

        assert 'graph' in dot
        assert 'digraph' not in dot
        assert '--' in dot

    def test_custom_name(self, simple_graph):
        """Custom graph name."""
        dot = to_dot(simple_graph, name="MyGraph")

        assert 'digraph MyGraph' in dot

    def test_rankdir(self, simple_graph):
        """Custom rank direction."""
        dot = to_dot(simple_graph, rankdir="LR")

        assert 'rankdir=LR' in dot

    def test_graph_attrs(self, simple_graph):
        """Custom graph attributes."""
        dot = to_dot(simple_graph, graph_attrs={"bgcolor": "white"})

        assert 'bgcolor' in dot

    def test_include_weights(self, simple_graph):
        """Include edge weights."""
        dot = to_dot(simple_graph, include_weights=True)

        assert '1.5' in dot
        assert '2.5' in dot

    def test_exclude_weights(self, simple_graph):
        """Exclude edge weights."""
        dot = to_dot(simple_graph, include_weights=False)

        # Weights should not appear as labels
        # Note: weight=1.0 edges won't show weight anyway
        assert 'label=' not in dot or '1.5' not in dot

    def test_custom_node_attrs(self, simple_graph):
        """Custom node attributes function."""
        dot = to_dot(
            simple_graph,
            node_attrs=lambda v: {"shape": "box", "fillcolor": v.get('color')}
        )

        assert 'shape=box' in dot
        assert 'fillcolor=red' in dot

    def test_custom_edge_attrs(self, simple_graph):
        """Custom edge attributes function."""
        dot = to_dot(
            simple_graph,
            edge_attrs=lambda e: {"style": "dashed"}
        )

        assert 'style=dashed' in dot

    def test_spaces_in_names(self, graph_with_spaces):
        """Handle spaces in vertex names."""
        dot = to_dot(graph_with_spaces)

        assert '"Node A"' in dot
        assert '"Node B"' in dot

    def test_dot_syntax_valid(self, simple_graph):
        """DOT output has valid syntax."""
        dot = to_dot(simple_graph)

        # Should start with graph type and end with }
        lines = dot.strip().split('\n')
        assert lines[0].startswith('digraph')
        assert lines[-1] == '}'

        # Should have matching braces
        assert dot.count('{') == dot.count('}')


# ============================================================================
# D3.js JSON Tests
# ============================================================================

class TestD3JsonExport:
    """Tests for D3.js JSON export."""

    def test_basic_d3_export(self, simple_graph):
        """Basic D3.js export."""
        data = to_d3_json(simple_graph)

        assert 'nodes' in data
        assert 'links' in data
        assert len(data['nodes']) == 3
        assert len(data['links']) == 2

    def test_node_ids(self, simple_graph):
        """Nodes have correct IDs."""
        data = to_d3_json(simple_graph)

        ids = {n['id'] for n in data['nodes']}
        assert ids == {'A', 'B', 'C'}

    def test_node_attributes(self, simple_graph):
        """Nodes include vertex attributes."""
        data = to_d3_json(simple_graph)

        node_a = next(n for n in data['nodes'] if n['id'] == 'A')
        assert node_a['color'] == 'red'
        assert node_a['size'] == 10

    def test_link_structure(self, simple_graph):
        """Links have correct structure."""
        data = to_d3_json(simple_graph)

        for link in data['links']:
            assert 'source' in link
            assert 'target' in link
            assert 'value' in link

    def test_link_weights(self, simple_graph):
        """Links include edge weights."""
        data = to_d3_json(simple_graph)

        ab_link = next(l for l in data['links'] if l['source'] == 'A')
        assert ab_link['value'] == 1.5

    def test_custom_node_attrs(self, simple_graph):
        """Custom node attributes."""
        data = to_d3_json(
            simple_graph,
            node_attrs=lambda v: {"group": 1 if v.get('size', 0) > 15 else 0}
        )

        node_a = next(n for n in data['nodes'] if n['id'] == 'A')
        assert node_a['group'] == 0  # size=10 < 15

        node_b = next(n for n in data['nodes'] if n['id'] == 'B')
        assert node_b['group'] == 1  # size=20 > 15

    def test_custom_link_attrs(self, simple_graph):
        """Custom link attributes."""
        data = to_d3_json(
            simple_graph,
            link_attrs=lambda e: {"color": "red" if e.weight > 2 else "blue"}
        )

        ab_link = next(l for l in data['links'] if l['source'] == 'A')
        assert ab_link['color'] == 'blue'  # weight=1.5 < 2

        bc_link = next(l for l in data['links'] if l['source'] == 'B')
        assert bc_link['color'] == 'red'  # weight=2.5 > 2

    def test_json_serializable(self, simple_graph):
        """Output is JSON serializable."""
        data = to_d3_json(simple_graph)
        # Should not raise
        json_str = json.dumps(data)
        assert len(json_str) > 0


# ============================================================================
# D3.js Hierarchical Tests
# ============================================================================

class TestD3HierarchicalExport:
    """Tests for D3.js hierarchical export."""

    def test_basic_hierarchical(self, tree_graph):
        """Basic hierarchical export."""
        data = to_d3_hierarchical(tree_graph, root='root')

        assert data['name'] == 'root'
        assert 'children' in data

    def test_hierarchy_structure(self, tree_graph):
        """Correct hierarchy structure."""
        data = to_d3_hierarchical(tree_graph, root='root')

        # Root has two children
        assert len(data['children']) == 2

        # child1 has two grandchildren
        child1 = next(c for c in data['children'] if c['name'] == 'child1')
        assert len(child1['children']) == 2

    def test_leaf_nodes(self, tree_graph):
        """Leaf nodes don't have children key."""
        data = to_d3_hierarchical(tree_graph, root='root')

        child2 = next(c for c in data['children'] if c['name'] == 'child2')
        # child2 has no outgoing edges
        assert 'children' not in child2 or len(child2.get('children', [])) == 0

    def test_custom_attrs(self, tree_graph):
        """Custom attributes in hierarchical."""
        data = to_d3_hierarchical(
            tree_graph,
            root='root',
            node_attrs=lambda v: {"value": 100}
        )

        assert data['value'] == 100


# ============================================================================
# Mermaid Tests
# ============================================================================

class TestMermaidExport:
    """Tests for Mermaid flowchart export."""

    def test_basic_mermaid(self, simple_graph):
        """Basic Mermaid export."""
        mermaid = to_mermaid(simple_graph)

        assert 'flowchart' in mermaid
        assert '-->' in mermaid

    def test_direction(self, simple_graph):
        """Custom flow direction."""
        mermaid = to_mermaid(simple_graph, direction="LR")

        assert 'flowchart LR' in mermaid

    def test_node_shapes(self, simple_graph):
        """Different node shapes."""
        # Rectangle
        rect = to_mermaid(simple_graph, node_shape="rect")
        assert '[' in rect

        # Round
        round_m = to_mermaid(simple_graph, node_shape="round")
        assert '(' in round_m

        # Circle
        circle = to_mermaid(simple_graph, node_shape="circle")
        assert '((' in circle

    def test_include_weights(self, simple_graph):
        """Include edge weights."""
        mermaid = to_mermaid(simple_graph, include_weights=True)

        assert '|1.5|' in mermaid
        assert '|2.5|' in mermaid

    def test_exclude_weights(self, simple_graph):
        """Exclude edge weights."""
        # Create graph with all weight=1.0 edges
        g = Graph(
            vertices={Vertex('A'), Vertex('B')},
            edges={Edge('A', 'B', weight=1.0)}
        )
        mermaid = to_mermaid(g, include_weights=True)

        # Weight 1.0 should not be shown
        assert '|' not in mermaid

    def test_spaces_in_names(self, graph_with_spaces):
        """Handle spaces in vertex names."""
        mermaid = to_mermaid(graph_with_spaces)

        # Spaces should be converted to underscores
        assert 'Node_A' in mermaid
        assert 'Node_B' in mermaid


# ============================================================================
# Adjacency JSON Tests
# ============================================================================

class TestAdjacencyJsonExport:
    """Tests for adjacency list JSON export."""

    def test_basic_adjacency(self, simple_graph):
        """Basic adjacency export."""
        data = to_adjacency_json(simple_graph)

        assert 'vertices' in data
        assert 'adjacency' in data

    def test_vertex_attrs(self, simple_graph):
        """Vertices include attributes."""
        data = to_adjacency_json(simple_graph)

        assert data['vertices']['A']['attrs']['color'] == 'red'

    def test_adjacency_lists(self, simple_graph):
        """Adjacency lists are correct."""
        data = to_adjacency_json(simple_graph)

        assert 'B' in data['adjacency']['A']
        assert 'C' in data['adjacency']['B']


# ============================================================================
# Cytoscape.js Tests
# ============================================================================

class TestCytoscapeExport:
    """Tests for Cytoscape.js export."""

    def test_basic_cytoscape(self, simple_graph):
        """Basic Cytoscape export."""
        data = to_cytoscape_json(simple_graph)

        assert 'elements' in data
        assert 'nodes' in data['elements']
        assert 'edges' in data['elements']

    def test_node_data(self, simple_graph):
        """Nodes have correct data."""
        data = to_cytoscape_json(simple_graph)

        for node in data['elements']['nodes']:
            assert 'data' in node
            assert 'id' in node['data']

    def test_edge_data(self, simple_graph):
        """Edges have correct data."""
        data = to_cytoscape_json(simple_graph)

        for edge in data['elements']['edges']:
            assert 'data' in edge
            assert 'source' in edge['data']
            assert 'target' in edge['data']


# ============================================================================
# Sigma.js Tests
# ============================================================================

class TestSigmaExport:
    """Tests for Sigma.js export."""

    def test_basic_sigma(self, simple_graph):
        """Basic Sigma export."""
        data = to_sigma_json(simple_graph)

        assert 'nodes' in data
        assert 'edges' in data

    def test_node_positions(self, simple_graph):
        """Nodes have positions."""
        data = to_sigma_json(simple_graph)

        for node in data['nodes']:
            assert 'x' in node
            assert 'y' in node

    def test_custom_layout(self, simple_graph):
        """Custom layout positions."""
        layout = {
            'A': {'x': 0, 'y': 0},
            'B': {'x': 100, 'y': 100},
            'C': {'x': 200, 'y': 0},
        }
        data = to_sigma_json(simple_graph, layout=layout)

        node_a = next(n for n in data['nodes'] if n['id'] == 'A')
        assert node_a['x'] == 0
        assert node_a['y'] == 0


# ============================================================================
# File Save Tests
# ============================================================================

class TestFileSave:
    """Tests for file save functions."""

    def test_save_dot(self, simple_graph):
        """Save DOT file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            filepath = f.name

        try:
            save_dot(simple_graph, filepath)
            with open(filepath) as f:
                content = f.read()
            assert 'digraph' in content
        finally:
            os.unlink(filepath)

    def test_save_d3_json(self, simple_graph):
        """Save D3.js JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name

        try:
            save_d3_json(simple_graph, filepath)
            with open(filepath) as f:
                data = json.load(f)
            assert 'nodes' in data
        finally:
            os.unlink(filepath)

    def test_save_mermaid(self, simple_graph):
        """Save Mermaid file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
            filepath = f.name

        try:
            save_mermaid(simple_graph, filepath)
            with open(filepath) as f:
                content = f.read()
            assert 'flowchart' in content
        finally:
            os.unlink(filepath)


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_graph(self):
        """Export empty graph."""
        g = Graph(vertices=set(), edges=set())

        dot = to_dot(g)
        assert 'digraph' in dot

        data = to_d3_json(g)
        assert data['nodes'] == []
        assert data['links'] == []

        mermaid = to_mermaid(g)
        assert 'flowchart' in mermaid

    def test_single_vertex(self):
        """Export single vertex graph."""
        g = Graph(vertices={Vertex('A')}, edges=set())

        dot = to_dot(g)
        assert 'A' in dot

        data = to_d3_json(g)
        assert len(data['nodes']) == 1

    def test_self_loop(self):
        """Export graph with self-loop."""
        g = Graph(
            vertices={Vertex('A')},
            edges={Edge('A', 'A', weight=1.0)}
        )

        dot = to_dot(g)
        assert 'A -> A' in dot

    def test_special_characters(self):
        """Handle special characters in names."""
        g = Graph(
            vertices={Vertex('A"B'), Vertex("C'D")},
            edges={Edge('A"B', "C'D")}
        )

        # Should not raise
        dot = to_dot(g)
        assert len(dot) > 0

        data = to_d3_json(g)
        assert len(data['nodes']) == 2
