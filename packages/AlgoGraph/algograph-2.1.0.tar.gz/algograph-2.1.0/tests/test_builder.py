"""
Tests for GraphBuilder fluent API.
"""

import pytest
from AlgoGraph import Graph, Vertex, Edge, GraphBuilder


class TestGraphBuilder:
    """Tests for GraphBuilder class."""

    def test_empty_builder(self):
        """Test building an empty graph."""
        g = GraphBuilder().build()
        assert g.vertex_count == 0
        assert g.edge_count == 0

    def test_add_single_vertex(self):
        """Test adding a single vertex."""
        g = GraphBuilder().add_vertex('A').build()
        assert g.vertex_count == 1
        assert g.has_vertex('A')

    def test_add_vertex_with_attributes(self):
        """Test adding vertex with attributes."""
        g = GraphBuilder().add_vertex('A', value=10, color='red').build()
        v = g.get_vertex('A')
        assert v.attrs['value'] == 10
        assert v.attrs['color'] == 'red'

    def test_add_multiple_vertices(self):
        """Test adding multiple vertices."""
        g = GraphBuilder().add_vertices('A', 'B', 'C').build()
        assert g.vertex_count == 3
        assert g.has_vertex('A')
        assert g.has_vertex('B')
        assert g.has_vertex('C')

    def test_add_vertices_with_common_attrs(self):
        """Test adding multiple vertices with common attributes."""
        g = GraphBuilder().add_vertices('A', 'B', 'C', layer=1).build()
        for vid in ['A', 'B', 'C']:
            v = g.get_vertex(vid)
            assert v.attrs['layer'] == 1

    def test_add_single_edge(self):
        """Test adding a single edge."""
        g = GraphBuilder().add_edge('A', 'B').build()
        assert g.vertex_count == 2
        assert g.edge_count == 1
        assert g.has_edge('A', 'B')

    def test_add_edge_with_weight(self):
        """Test adding edge with weight."""
        g = GraphBuilder().add_edge('A', 'B', weight=5.0).build()
        edge = g.get_edge('A', 'B')
        assert edge.weight == 5.0

    def test_add_edge_with_attributes(self):
        """Test adding edge with attributes."""
        g = GraphBuilder().add_edge('A', 'B', weight=5.0, label='connection').build()
        edge = g.get_edge('A', 'B')
        assert edge.attrs['label'] == 'connection'

    def test_add_undirected_edge(self):
        """Test adding undirected edge."""
        g = GraphBuilder().add_edge('A', 'B', directed=False).build()
        edge = g.get_edge('A', 'B')
        assert not edge.directed

    def test_add_multiple_edges(self):
        """Test adding multiple edges."""
        g = GraphBuilder().add_edges(('A', 'B'), ('B', 'C'), ('C', 'D')).build()
        assert g.edge_count == 3
        assert g.has_edge('A', 'B')
        assert g.has_edge('B', 'C')
        assert g.has_edge('C', 'D')

    def test_chaining(self):
        """Test method chaining."""
        g = (GraphBuilder()
             .add_vertex('A', value=1)
             .add_vertex('B', value=2)
             .add_edge('A', 'B', weight=5)
             .build())

        assert g.vertex_count == 2
        assert g.edge_count == 1
        assert g.get_vertex('A').attrs['value'] == 1
        assert g.get_edge('A', 'B').weight == 5

    def test_add_path(self):
        """Test adding a path."""
        g = GraphBuilder().add_path('A', 'B', 'C', 'D').build()

        assert g.vertex_count == 4
        assert g.edge_count == 3
        assert g.has_edge('A', 'B')
        assert g.has_edge('B', 'C')
        assert g.has_edge('C', 'D')
        assert not g.has_edge('D', 'A')  # Not a cycle

    def test_add_path_undirected(self):
        """Test adding undirected path."""
        g = GraphBuilder().add_path('A', 'B', 'C', directed=False).build()

        assert g.vertex_count == 3
        # All edges should be undirected
        assert not g.get_edge('A', 'B').directed
        assert not g.get_edge('B', 'C').directed

    def test_add_cycle(self):
        """Test adding a cycle."""
        g = GraphBuilder().add_cycle('A', 'B', 'C').build()

        assert g.vertex_count == 3
        assert g.edge_count == 3
        assert g.has_edge('A', 'B')
        assert g.has_edge('B', 'C')
        assert g.has_edge('C', 'A')  # Closes the cycle

    def test_add_complete_graph(self):
        """Test adding a complete graph (clique)."""
        g = GraphBuilder().add_complete('A', 'B', 'C', 'D').build()

        assert g.vertex_count == 4
        # Complete graph on 4 vertices has 6 edges
        assert g.edge_count == 6

        # Check all pairs are connected
        vertices = ['A', 'B', 'C', 'D']
        for i, v1 in enumerate(vertices):
            for v2 in vertices[i+1:]:
                assert g.has_edge(v1, v2) or g.has_edge(v2, v1)

    def test_add_star_graph(self):
        """Test adding a star graph."""
        g = GraphBuilder().add_star('Hub', 'A', 'B', 'C', 'D').build()

        assert g.vertex_count == 5
        # 4 edges from hub to satellites
        assert g.edge_count == 4

        # Check hub is connected to all satellites
        for satellite in ['A', 'B', 'C', 'D']:
            assert g.has_edge('Hub', satellite)

    def test_add_bipartite(self):
        """Test adding bipartite structure."""
        g = GraphBuilder().add_bipartite(['A', 'B'], ['X', 'Y'], complete=False).build()

        assert g.vertex_count == 4
        # Just vertices, no edges yet
        assert g.edge_count == 0

        # Check partitions
        assert g.get_vertex('A').attrs['partition'] == 'left'
        assert g.get_vertex('X').attrs['partition'] == 'right'

    def test_add_complete_bipartite(self):
        """Test adding complete bipartite graph."""
        g = GraphBuilder().add_bipartite(['A', 'B'], ['X', 'Y', 'Z'], complete=True).build()

        assert g.vertex_count == 5
        # 2*3 = 6 edges
        assert g.edge_count == 6

        # Check all cross-partition edges exist
        for left in ['A', 'B']:
            for right in ['X', 'Y', 'Z']:
                assert g.has_edge(left, right)

    def test_repr(self):
        """Test string representation."""
        builder = GraphBuilder().add_vertex('A').add_edge('A', 'B')
        repr_str = repr(builder)
        assert 'GraphBuilder' in repr_str
        assert 'vertices=2' in repr_str
        assert 'edges=1' in repr_str


class TestGraphClassMethods:
    """Tests for Graph class methods."""

    def test_builder_classmethod(self):
        """Test Graph.builder() classmethod."""
        g = (Graph.builder()
             .add_vertex('A')
             .add_edge('A', 'B')
             .build())

        assert isinstance(g, Graph)
        assert g.vertex_count == 2
        assert g.edge_count == 1

    def test_from_edges(self):
        """Test Graph.from_edges()."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'D'))

        assert g.vertex_count == 4
        assert g.edge_count == 3
        assert g.has_edge('A', 'B')
        assert g.has_edge('B', 'C')
        assert g.has_edge('C', 'D')

    def test_from_edges_undirected(self):
        """Test Graph.from_edges() with undirected edges."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), directed=False)

        assert g.edge_count == 2
        assert not g.get_edge('A', 'B').directed

    def test_from_edges_with_weight(self):
        """Test Graph.from_edges() with weight."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), weight=5.0)

        edge = g.get_edge('A', 'B')
        assert edge.weight == 5.0

    def test_from_vertices(self):
        """Test Graph.from_vertices()."""
        g = Graph.from_vertices('A', 'B', 'C', 'D')

        assert g.vertex_count == 4
        assert g.edge_count == 0
        assert g.has_vertex('A')
        assert g.has_vertex('D')

    def test_from_vertices_with_attrs(self):
        """Test Graph.from_vertices() with attributes."""
        g = Graph.from_vertices('A', 'B', 'C', layer=1, active=True)

        for vid in ['A', 'B', 'C']:
            v = g.get_vertex(vid)
            assert v.attrs['layer'] == 1
            assert v.attrs['active'] is True


class TestBuilderComplexGraphs:
    """Tests for building complex graph structures."""

    def test_social_network(self):
        """Test building a social network graph."""
        g = (GraphBuilder()
             .add_vertex('Alice', age=30, city='NYC')
             .add_vertex('Bob', age=25, city='Boston')
             .add_vertex('Charlie', age=35, city='Seattle')
             .add_edge('Alice', 'Bob', directed=False, relationship='friend')
             .add_edge('Bob', 'Charlie', directed=False, relationship='friend')
             .build())

        assert g.vertex_count == 3
        assert g.edge_count == 2

        alice = g.get_vertex('Alice')
        assert alice.attrs['age'] == 30
        assert alice.attrs['city'] == 'NYC'

        friendship = g.get_edge('Alice', 'Bob')
        assert not friendship.directed
        assert friendship.attrs['relationship'] == 'friend'

    def test_dependency_graph(self):
        """Test building a dependency graph."""
        g = (GraphBuilder()
             .add_vertices('app', 'lib1', 'lib2', 'utils')
             .add_edge('app', 'lib1', directed=True)
             .add_edge('app', 'lib2', directed=True)
             .add_edge('lib1', 'utils', directed=True)
             .add_edge('lib2', 'utils', directed=True)
             .build())

        assert g.vertex_count == 4
        assert g.edge_count == 4
        assert g.is_directed

        # Check dependencies
        assert 'lib1' in g.neighbors('app')
        assert 'utils' in g.neighbors('lib1')

    def test_road_network(self):
        """Test building a road network graph."""
        g = (GraphBuilder()
             .add_vertex('NYC', population=8000000)
             .add_vertex('Boston', population=700000)
             .add_vertex('DC', population=700000)
             .add_edge('NYC', 'Boston', directed=False, weight=215, highway='I-95')
             .add_edge('NYC', 'DC', directed=False, weight=225, highway='I-95')
             .build())

        assert g.vertex_count == 3
        assert g.edge_count == 2

        road = g.get_edge('NYC', 'Boston')
        assert road.weight == 215
        assert road.attrs['highway'] == 'I-95'
        assert not road.directed


class TestBuilderEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_path(self):
        """Test adding empty path."""
        g = GraphBuilder().add_path().build()
        assert g.vertex_count == 0

    def test_single_vertex_path(self):
        """Test adding path with single vertex."""
        g = GraphBuilder().add_path('A').build()
        assert g.vertex_count == 1
        assert g.edge_count == 0

    def test_empty_cycle(self):
        """Test adding empty cycle."""
        g = GraphBuilder().add_cycle().build()
        assert g.vertex_count == 0

    def test_duplicate_vertices(self):
        """Test adding duplicate vertices (should update)."""
        g = (GraphBuilder()
             .add_vertex('A', value=1)
             .add_vertex('A', value=2)  # Updates attributes
             .build())

        assert g.vertex_count == 1
        v = g.get_vertex('A')
        assert v.attrs['value'] == 2

    def test_auto_create_vertices_from_edges(self):
        """Test that vertices are auto-created from edges."""
        g = GraphBuilder().add_edge('A', 'B').build()

        # Vertices should be created automatically
        assert g.vertex_count == 2
        assert g.has_vertex('A')
        assert g.has_vertex('B')
