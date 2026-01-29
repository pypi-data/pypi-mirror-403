"""
Additional tests for Phase 3 features to improve coverage.

This test file addresses gaps identified in coverage analysis:
- XorSelector and other uncovered selector types
- Selector utility methods (first, count, exists, ids)
- MinimumSpanningTreeTransformer
- ComponentView and view convenience functions
- Edge cases and error conditions
"""

import pytest
from AlgoGraph import Vertex, Edge, Graph
from AlgoGraph.transformers import (
    filter_vertices, filter_edges, minimum_spanning_tree,
    Pipeline, stats
)
from AlgoGraph.graph_selectors import (
    vertex, edge, VertexNeighborSelector, EdgeSourceSelector,
    EdgeTargetSelector, EdgeAttrsSelector
)
from AlgoGraph.views import (
    ComponentView, reversed_view, undirected_view,
    component_view, neighborhood_view, filtered_view, subgraph_view
)


class TestSelectorCoverage:
    """Tests for uncovered selector functionality."""

    def test_xor_selector(self):
        """Test XOR combinator for selectors."""
        g = (Graph.builder()
             .add_vertex('A', age=30, active=True)
             .add_vertex('B', age=25, active=False)
             .add_vertex('C', age=35, active=True)
             .add_vertex('D', age=20, active=False)
             .build())

        # XOR: young OR active, but not both
        young = vertex.attrs(age=lambda a: a < 28)
        active = vertex.attrs(active=True)

        sel = young ^ active
        matches = g.select_vertices(sel)

        # Should match C (active but not young) and B,D (young but not active)
        ids = {v.id for v in matches}
        assert 'C' in ids  # Active but not young (age=35)
        assert 'B' in ids or 'D' in ids  # Young but not active

    def test_vertex_neighbor_selector(self):
        """Test VertexNeighborSelector - find vertices with matching neighbors."""
        g = (Graph.builder()
             .add_vertex('A', role='admin')
             .add_vertex('B', role='user')
             .add_vertex('C', role='user')
             .add_edge('A', 'B', directed=False)  # Admin connected to B
             .add_edge('B', 'C', directed=False)  # User connected to another user
             .build())

        # Find vertices that have an admin neighbor
        admin_sel = vertex.attrs(role='admin')
        has_admin_neighbor = VertexNeighborSelector(admin_sel)

        matches = list(has_admin_neighbor.select(g))

        assert len(matches) == 1
        assert matches[0].id == 'B'  # B is connected to admin A

    def test_edge_source_selector(self):
        """Test EdgeSourceSelector - select edges by source vertex properties."""
        g = (Graph.builder()
             .add_vertex('admin_1', role='admin')
             .add_vertex('admin_2', role='admin')
             .add_vertex('user_1', role='user')
             .add_edge('admin_1', 'user_1')
             .add_edge('user_1', 'admin_2')
             .build())

        # Find edges originating from admin vertices
        admin_source = EdgeSourceSelector(vertex.attrs(role='admin'))
        matches = list(admin_source.select(g))

        assert len(matches) == 1
        assert matches[0].source == 'admin_1'

    def test_edge_target_selector(self):
        """Test EdgeTargetSelector - select edges by target vertex properties."""
        g = (Graph.builder()
             .add_vertex('A', priority='high')
             .add_vertex('B', priority='low')
             .add_vertex('C', priority='high')
             .add_edge('A', 'B')
             .add_edge('B', 'C')
             .build())

        # Find edges targeting high-priority vertices
        high_target = EdgeTargetSelector(vertex.attrs(priority='high'))
        matches = list(high_target.select(g))

        assert len(matches) == 1
        assert matches[0].target == 'C'

    def test_edge_attrs_selector(self):
        """Test EdgeAttrsSelector - select edges by attributes."""
        g = (Graph.builder()
             .add_edge('A', 'B', type='fiber', capacity=1000)
             .add_edge('B', 'C', type='copper', capacity=100)
             .add_edge('C', 'D', type='fiber', capacity=1000)
             .build())

        # Find fiber edges with high capacity
        sel = edge.attrs(type='fiber', capacity=lambda c: c >= 1000)
        matches = g.select_edges(sel)

        assert len(matches) == 2

    def test_selector_first_method(self):
        """Test Selector.first() method."""
        g = Graph.from_vertices('A', 'B', 'C')

        sel = vertex.id('B')
        first = sel.first(g)

        assert first is not None
        assert first.id == 'B'

        # Test first() with no matches
        no_match = vertex.id('nonexistent')
        assert no_match.first(g) is None

    def test_selector_count_method(self):
        """Test Selector.count() method."""
        g = Graph.from_vertices('user_1', 'user_2', 'admin_1')

        sel = vertex.id('user_*')
        count = sel.count(g)

        assert count == 2

    def test_selector_exists_method(self):
        """Test Selector.exists() method."""
        g = Graph.from_vertices('A', 'B')

        assert vertex.id('A').exists(g) is True
        assert vertex.id('Z').exists(g) is False

    def test_vertex_selector_ids_method(self):
        """Test VertexSelector.ids() method."""
        g = Graph.from_vertices('A', 'B', 'C')

        sel = vertex.id('*')
        ids = sel.ids(g)

        assert ids == {'A', 'B', 'C'}

    def test_selector_requires_graph_context(self):
        """Test selectors that require graph context fail without it."""
        v = Vertex('A')

        deg_sel = vertex.degree(min_degree=1)

        with pytest.raises(ValueError, match="requires graph context"):
            deg_sel.matches(v, graph=None)

    def test_vertex_id_selector_regex(self):
        """Test VertexIdSelector with regex patterns."""
        g = Graph.from_vertices('user_123', 'user_456', 'admin_789')

        # Regex pattern for user IDs with digits
        sel = vertex.id(r'user_\d+')
        matches = g.select_vertices(sel)

        assert len(matches) == 2


class TestTransformerCoverage:
    """Tests for uncovered transformer functionality."""

    def test_minimum_spanning_tree_transformer(self):
        """Test MinimumSpanningTreeTransformer."""
        g = (Graph.builder()
             .add_edge('A', 'B', weight=4, directed=False)
             .add_edge('B', 'C', weight=8, directed=False)
             .add_edge('C', 'D', weight=7, directed=False)
             .add_edge('D', 'A', weight=11, directed=False)
             .add_edge('A', 'C', weight=2, directed=False)
             .build())

        result = g | minimum_spanning_tree()

        # MST should have n-1 edges for n vertices
        assert result.vertex_count == 4
        assert result.edge_count == 3

        # Check total MST weight is minimal
        total_weight = sum(e.weight for e in result.edges)
        assert total_weight == 13.0  # A-C(2) + A-B(4) + C-D(7)

    def test_conditional_transformer_false_condition(self):
        """Test ConditionalTransformer when condition is False."""
        g = Graph.from_vertices('A', 'B')

        # Condition that will be False (vertex_count > 5)
        transform = filter_vertices(lambda v: v.id == 'A').when(
            lambda g: g.vertex_count > 5
        )

        result = g | transform

        # Graph should be unchanged since condition is False
        assert result.vertex_count == 2
        assert result == g

    def test_pipeline_repr(self):
        """Test Pipeline.__repr__() method."""
        pipe = Pipeline(
            filter_vertices(lambda v: True),
            filter_edges(lambda e: True)
        )

        repr_str = repr(pipe)
        assert 'Pipeline' in repr_str

    def test_pipeline_direct_composition(self):
        """Test Pipeline creation via | operator on transformers."""
        t1 = filter_vertices(lambda v: v.id in {'A', 'B'})
        t2 = filter_edges(lambda e: e.weight > 5)

        # Compose transformers directly
        pipeline = t1 | t2

        assert isinstance(pipeline, Pipeline)
        assert len(pipeline.transformers) == 2

    def test_empty_graph_through_complex_pipeline(self):
        """Test complex pipeline on empty graph."""
        g = Graph()

        result = g | filter_vertices(lambda v: True) | stats()

        assert result['vertex_count'] == 0
        assert result['edge_count'] == 0


class TestViewCoverage:
    """Tests for uncovered view functionality."""

    def test_component_view(self):
        """Test ComponentView for connected components."""
        g = (Graph.builder()
             .add_edge('A', 'B', directed=False)
             .add_edge('B', 'C', directed=False)
             .add_edge('D', 'E', directed=False)
             .build())

        # View of first component
        comp1_view = ComponentView(g, {'A', 'B', 'C'})

        assert comp1_view.vertex_count == 3
        assert comp1_view.edge_count == 2

        # Materialize and verify
        comp1_graph = comp1_view.materialize()
        assert comp1_graph.vertex_count == 3

    def test_component_view_convenience_function(self):
        """Test component_view() convenience function."""
        g = (Graph.builder()
             .add_edge('A', 'B', directed=False)
             .add_edge('C', 'D', directed=False)
             .build())

        view = component_view(g, {'A', 'B'})

        assert view.vertex_count == 2
        assert view.edge_count == 1

    def test_reversed_view_convenience(self):
        """Test reversed_view() convenience function."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'))

        view = reversed_view(g)
        edges = list(view.edges())

        assert len(edges) == 2
        assert any(e.source == 'B' and e.target == 'A' for e in edges)

    def test_undirected_view_convenience(self):
        """Test undirected_view() convenience function."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'))

        view = undirected_view(g)
        edges = list(view.edges())

        assert all(not e.directed for e in edges)

    def test_neighborhood_view_convenience(self):
        """Test neighborhood_view() convenience function."""
        g = (Graph.builder()
             .add_path('A', 'B', 'C', 'D', directed=False)
             .build())

        view = neighborhood_view(g, 'B', k=1)

        assert view.vertex_count == 3  # A, B, C

    def test_neighborhood_view_zero_hops(self):
        """Test NeighborhoodView with k=0 (just the center vertex)."""
        g = (Graph.builder()
             .add_path('A', 'B', 'C', directed=False)
             .build())

        view = neighborhood_view(g, 'B', k=0)

        assert view.vertex_count == 1
        vertices = list(view.vertices())
        assert vertices[0].id == 'B'

    def test_neighborhood_view_unreachable(self):
        """Test NeighborhoodView with disconnected components."""
        g = (Graph.builder()
             .add_edge('A', 'B', directed=False)
             .add_edge('C', 'D', directed=False)  # Disconnected
             .build())

        view = neighborhood_view(g, 'A', k=10)

        # Should only include A-B component, not C-D
        assert view.vertex_count == 2
        vertex_ids = {v.id for v in view.vertices()}
        assert vertex_ids == {'A', 'B'}

    def test_filtered_view_edge_filter_only(self):
        """Test FilteredView with only edge filter (no vertex filter)."""
        g = (Graph.builder()
             .add_edge('A', 'B', weight=5)
             .add_edge('B', 'C', weight=10)
             .build())

        view = filtered_view(g, edge_filter=lambda e: e.weight > 7)

        assert view.vertex_count == 3  # All vertices present
        assert view.edge_count == 1    # Only heavy edge

    def test_filtered_view_repr(self):
        """Test FilteredView.__repr__() with different filter combinations."""
        g = Graph.from_vertices('A', 'B')

        # No filters
        view1 = filtered_view(g)
        repr1 = repr(view1)
        assert 'no filters' in repr1

        # Vertex filter only
        view2 = filtered_view(g, vertex_filter=lambda v: True)
        repr2 = repr(view2)
        assert 'vertex_filter' in repr2

        # Both filters
        view3 = filtered_view(
            Graph.from_edges(('A', 'B')),
            vertex_filter=lambda v: True,
            edge_filter=lambda e: True
        )
        repr3 = repr(view3)
        assert 'vertex_filter' in repr3
        assert 'edge_filter' in repr3

    def test_graph_view_graph_property(self):
        """Test GraphView.graph property accessor."""
        g = Graph.from_vertices('A', 'B')
        view = filtered_view(g)

        assert view.graph is g

    def test_view_on_empty_graph(self):
        """Test views on empty graphs."""
        g = Graph()

        # FilteredView on empty graph
        fv = filtered_view(g, vertex_filter=lambda v: True)
        assert fv.vertex_count == 0

        # SubGraphView on empty graph
        from AlgoGraph.views import SubGraphView
        sv = SubGraphView(g, set())
        assert sv.vertex_count == 0

        # ReversedView on empty graph
        rv = reversed_view(g)
        assert rv.vertex_count == 0


class TestIntegrationCoverage:
    """Integration tests combining multiple features."""

    def test_selectors_with_views(self):
        """Test using selectors to create views."""
        g = (Graph.builder()
             .add_vertex('A', active=True, score=90)
             .add_vertex('B', active=False, score=75)
             .add_vertex('C', active=True, score=60)
             .add_vertex('D', active=True, score=85)
             .add_edge('A', 'D', directed=False)
             .add_edge('B', 'C', directed=False)
             .build())

        # Use selector to find high-scoring active vertices
        high_performers = vertex.attrs(active=True) & vertex.attrs(
            score=lambda s: s > 80
        )
        ids = high_performers.ids(g)

        # Create subgraph view of high performers
        view = subgraph_view(g, ids)

        assert view.vertex_count == 2  # A and D
        assert view.edge_count == 1    # A-D edge

    def test_views_materialized_through_transformers(self):
        """Test materializing views and passing through transformers."""
        g = (Graph.builder()
             .add_vertex('A', value=10)
             .add_vertex('B', value=20)
             .add_vertex('C', value=30)
             .add_edge('A', 'B', weight=5)
             .add_edge('B', 'C', weight=15)
             .build())

        # Create filtered view
        view = filtered_view(g, edge_filter=lambda e: e.weight > 7)

        # Materialize and transform
        result = view.materialize() | stats()

        assert result['vertex_count'] == 3
        assert result['edge_count'] == 1

    def test_complex_selector_chain_with_transformers(self):
        """Test complex workflow: selectors -> views -> transformers."""
        g = (Graph.builder()
             .add_vertex('server_1', region='us-east', load=0.3)
             .add_vertex('server_2', region='us-east', load=0.8)
             .add_vertex('server_3', region='eu-west', load=0.5)
             .add_vertex('server_4', region='us-east', load=0.6)
             .add_edge('server_1', 'server_2', latency=10)
             .add_edge('server_2', 'server_4', latency=15)
             .add_edge('server_3', 'server_4', latency=100)
             .build())

        # Find healthy servers in us-east with low load
        us_east = vertex.attrs(region='us-east')
        low_load = vertex.attrs(load=lambda l: l < 0.7)
        healthy = us_east & low_load

        server_ids = healthy.ids(g)

        # Create view and analyze
        view = subgraph_view(g, server_ids)

        analysis = view.materialize() | stats()

        assert analysis['vertex_count'] == 2  # server_1 and server_4
