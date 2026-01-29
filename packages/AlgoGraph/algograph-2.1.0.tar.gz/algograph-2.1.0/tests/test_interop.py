"""
Tests for AlgoTree <-> AlgoGraph interoperability.

These tests require AlgoTree to be installed or available in PYTHONPATH.
They will be skipped if AlgoTree is not available.
"""

import pytest

# Try to import AlgoTree - tests will be skipped if not available
try:
    from AlgoTree import Node, Tree
    ALGOTREE_AVAILABLE = True
except ImportError:
    ALGOTREE_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="AlgoTree not available")

from AlgoGraph import (
    Vertex, Edge, Graph,
    tree_to_graph, node_to_graph, graph_to_tree,
    flat_dict_to_graph, graph_to_flat_dict
)


class TestTreeToGraph:
    """Tests for converting trees to graphs."""

    def test_simple_tree_to_graph(self):
        """Test converting simple tree to graph."""
        tree = Tree(Node('root',
            Node('child1'),
            Node('child2')
        ))

        graph = tree_to_graph(tree)

        assert graph.vertex_count == 3
        assert graph.edge_count == 2
        assert graph.has_vertex('root')
        assert graph.has_vertex('child1')
        assert graph.has_edge('root', 'child1')
        assert graph.has_edge('root', 'child2')

    def test_tree_with_attributes(self):
        """Test that node attributes are preserved."""
        tree = Tree(Node('root',
            Node('child', attrs={'value': 10, 'color': 'red'}),
            attrs={'root_attr': 'test'}
        ))

        graph = tree_to_graph(tree)

        root_vertex = graph.get_vertex('root')
        assert root_vertex.get('root_attr') == 'test'

        child_vertex = graph.get_vertex('child')
        assert child_vertex.get('value') == 10
        assert child_vertex.get('color') == 'red'

    def test_deep_tree_to_graph(self):
        """Test converting deep tree."""
        tree = Tree(Node('a',
            Node('b',
                Node('d'),
                Node('e')
            ),
            Node('c',
                Node('f')
            )
        ))

        graph = tree_to_graph(tree)

        assert graph.vertex_count == 6
        assert graph.edge_count == 5
        assert graph.has_edge('a', 'b')
        assert graph.has_edge('a', 'c')
        assert graph.has_edge('b', 'd')
        assert graph.has_edge('b', 'e')
        assert graph.has_edge('c', 'f')

    def test_undirected_option(self):
        """Test creating undirected graph from tree."""
        tree = Tree(Node('root', Node('child')))

        graph = tree_to_graph(tree, directed=False)

        edge = graph.get_edge('root', 'child')
        assert edge is not None
        assert not edge.directed


class TestGraphToTree:
    """Tests for converting graphs to trees."""

    def test_simple_graph_to_tree(self):
        """Test converting simple graph to tree."""
        vertices = {Vertex('root'), Vertex('child1'), Vertex('child2')}
        edges = {Edge('root', 'child1'), Edge('root', 'child2')}
        graph = Graph(vertices, edges)

        tree = graph_to_tree(graph, 'root')

        assert tree.root.name == 'root'
        assert len(tree.root.children) == 2
        child_names = {c.name for c in tree.root.children}
        assert child_names == {'child1', 'child2'}

    def test_graph_with_attributes(self):
        """Test that vertex attributes are preserved."""
        vertices = {
            Vertex('root', attrs={'value': 1}),
            Vertex('child', attrs={'value': 2})
        }
        edges = {Edge('root', 'child')}
        graph = Graph(vertices, edges)

        tree = graph_to_tree(graph, 'root')

        assert tree.root.get('value') == 1
        assert tree.root.children[0].get('value') == 2

    def test_invalid_root(self):
        """Test error when root not in graph."""
        graph = Graph({Vertex('A')})

        with pytest.raises(ValueError, match="Root vertex 'B' not in graph"):
            graph_to_tree(graph, 'B')


class TestRoundTrip:
    """Tests for tree -> graph -> tree conversion."""

    def test_round_trip_preserves_structure(self):
        """Test that round-trip conversion preserves structure."""
        original = Tree(Node('root',
            Node('a', Node('aa'), Node('ab')),
            Node('b', Node('ba'))
        ))

        graph = tree_to_graph(original)
        recovered = graph_to_tree(graph, 'root')

        # Check structure is preserved
        assert recovered.root.name == 'root'
        assert len(recovered.root.children) == 2

        # Check all nodes present
        names = {n.name for n in recovered.walk()}
        assert names == {'root', 'a', 'b', 'aa', 'ab', 'ba'}

    def test_round_trip_preserves_attributes(self):
        """Test that attributes are preserved through round-trip."""
        original = Tree(Node('root',
            Node('child', attrs={'x': 10, 'y': 'test'}),
            attrs={'root_val': 42}
        ))

        graph = tree_to_graph(original)
        recovered = graph_to_tree(graph, 'root')

        assert recovered.root.get('root_val') == 42
        child = [c for c in recovered.root.children if c.name == 'child'][0]
        assert child.get('x') == 10
        assert child.get('y') == 'test'


class TestFlatDictFormat:
    """Tests for flat dictionary format."""

    def test_graph_to_flat_dict(self):
        """Test converting graph to flat dict."""
        vertices = {Vertex('A', attrs={'value': 1}), Vertex('B')}
        edges = {Edge('A', 'B', weight=5.0)}
        graph = Graph(vertices, edges)

        flat = graph_to_flat_dict(graph)

        assert 'A' in flat
        assert 'B' in flat
        assert flat['A']['.name'] == 'A'
        assert flat['A']['value'] == 1
        assert len(flat['A']['.edges']) == 1
        assert flat['A']['.edges'][0]['target'] == 'B'
        assert flat['A']['.edges'][0]['weight'] == 5.0

    def test_flat_dict_to_graph(self):
        """Test converting flat dict to graph."""
        flat = {
            'A': {
                '.name': 'A',
                '.edges': [{'target': 'B', 'weight': 2.0, 'directed': True}],
                'value': 10
            },
            'B': {
                '.name': 'B',
                '.edges': [],
                'value': 20
            }
        }

        graph = flat_dict_to_graph(flat)

        assert graph.vertex_count == 2
        assert graph.edge_count == 1
        assert graph.has_edge('A', 'B')

        a = graph.get_vertex('A')
        assert a.get('value') == 10

    def test_flat_dict_round_trip(self):
        """Test round-trip through flat dict."""
        vertices = {
            Vertex('X', attrs={'a': 1}),
            Vertex('Y', attrs={'b': 2}),
            Vertex('Z', attrs={'c': 3})
        }
        edges = {
            Edge('X', 'Y', weight=1.5),
            Edge('Y', 'Z', weight=2.5)
        }
        original = Graph(vertices, edges)

        flat = graph_to_flat_dict(original)
        recovered = flat_dict_to_graph(flat)

        assert recovered.vertex_count == original.vertex_count
        assert recovered.edge_count == original.edge_count

        for vid in ['X', 'Y', 'Z']:
            orig_v = original.get_vertex(vid)
            rec_v = recovered.get_vertex(vid)
            assert orig_v.attrs == rec_v.attrs


class TestNodeToGraph:
    """Tests for node_to_graph convenience function."""

    def test_node_to_graph(self):
        """Test converting single node to graph."""
        node = Node('root', Node('child'))

        graph = node_to_graph(node)

        assert graph.vertex_count == 2
        assert graph.has_edge('root', 'child')
