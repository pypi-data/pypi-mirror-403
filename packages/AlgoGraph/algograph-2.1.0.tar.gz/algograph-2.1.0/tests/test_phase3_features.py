"""
Tests for Phase 3 features (transformers, selectors, views).
"""

import pytest

from AlgoGraph import Vertex, Edge, Graph
from AlgoGraph.transformers import (
    filter_vertices, filter_edges, map_vertices, map_edges,
    subgraph, reverse, to_undirected, largest_component,
    to_dict, to_adjacency_list, stats, Pipeline
)
from AlgoGraph.graph_selectors import (
    vertex, edge, VertexIdSelector, VertexAttrsSelector,
    VertexDegreeSelector, EdgeWeightSelector, EdgeDirectedSelector
)
from AlgoGraph.views import (
    FilteredView, SubGraphView, ReversedView, UndirectedView,
    NeighborhoodView, filtered_view, subgraph_view
)


class TestTransformers:
    """Tests for transformer pattern and built-in transformers."""

    def test_filter_vertices_transformer(self):
        """Test filter_vertices transformer."""
        g = Graph.from_vertices('A', 'B', 'C', value=10)
        g = g.add_vertex(Vertex('D', attrs={'value': 20}))

        result = g | filter_vertices(lambda v: v.get('value') == 20)

        assert result.vertex_count == 1
        assert result.has_vertex('D')

    def test_filter_edges_transformer(self):
        """Test filter_edges transformer."""
        g = (Graph.builder()
             .add_edge('A', 'B', weight=5)
             .add_edge('B', 'C', weight=10)
             .build())

        result = g | filter_edges(lambda e: e.weight > 7)

        assert result.edge_count == 1
        assert result.vertex_count == 3  # Vertices preserved

    def test_map_vertices_transformer(self):
        """Test map_vertices transformer."""
        g = Graph.from_vertices('A', 'B', 'C')

        result = g | map_vertices(lambda v: v.with_attrs(processed=True))

        for v in result.vertices:
            assert v.get('processed') == True

    def test_map_edges_transformer(self):
        """Test map_edges transformer."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), weight=5)

        result = g | map_edges(lambda e: e.with_weight(e.weight * 2))

        for e in result.edges:
            assert e.weight == 10.0

    def test_pipe_composition(self):
        """Test pipeline composition with | operator."""
        g = (Graph.builder()
             .add_vertices('A', 'B', 'C', 'D')
             .add_edge('A', 'B')
             .add_edge('B', 'C')
             .add_edge('C', 'D')
             .build())

        result = g | filter_vertices(lambda v: v.id in {'A', 'B', 'C'}) | to_dict()

        assert len(result['vertices']) == 3
        assert len(result['edges']) == 2

    def test_reverse_transformer(self):
        """Test reverse transformer."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'))

        result = g | reverse()

        assert result.has_edge('B', 'A')
        assert result.has_edge('C', 'B')
        assert not result.has_edge('A', 'B')

    def test_to_undirected_transformer(self):
        """Test to_undirected transformer."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'))

        result = g | to_undirected()

        for e in result.edges:
            assert not e.directed

    def test_largest_component_transformer(self):
        """Test largest_component transformer."""
        g = (Graph.builder()
             .add_edge('A', 'B', directed=False)
             .add_edge('C', 'D', directed=False)
             .add_edge('E', 'F', directed=False)
             .add_edge('F', 'G', directed=False)
             .build())

        result = g | largest_component()

        # Component with E-F-G is largest (3 vertices)
        assert result.vertex_count == 3

    def test_to_dict_transformer(self):
        """Test to_dict transformer."""
        g = Graph.from_edges(('A', 'B'), weight=5)

        result = g | to_dict()

        assert 'vertices' in result
        assert 'edges' in result
        assert len(result['vertices']) == 2
        assert len(result['edges']) == 1

    def test_to_adjacency_list_transformer(self):
        """Test to_adjacency_list transformer."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'))

        result = g | to_adjacency_list()

        assert 'A' in result
        assert 'B' in result['A']
        assert 'C' in result['B']

    def test_stats_transformer(self):
        """Test stats transformer."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'A'))

        result = g | stats()

        assert result['vertex_count'] == 3
        assert result['edge_count'] == 3
        assert 'density' in result
        assert 'avg_degree' in result

    def test_subgraph_transformer(self):
        """Test subgraph transformer."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'D'))

        result = g | subgraph({'A', 'B', 'C'})

        assert result.vertex_count == 3
        assert result.edge_count == 2

    def test_complex_pipeline(self):
        """Test complex transformation pipeline."""
        g = (Graph.builder()
             .add_vertices('A', 'B', 'C', 'D', value=10)
             .add_edge('A', 'B', weight=5)
             .add_edge('B', 'C', weight=15)
             .add_edge('C', 'D', weight=3)
             .build())

        result = (g
                  | filter_edges(lambda e: e.weight > 4)
                  | map_vertices(lambda v: v.with_attrs(doubled=v.get('value') * 2))
                  | to_dict())

        assert len(result['edges']) == 2  # Only weight > 4
        for v_dict in result['vertices']:
            assert v_dict['attrs']['doubled'] == 20


class TestSelectors:
    """Tests for selector pattern and built-in selectors."""

    def test_vertex_id_selector(self):
        """Test VertexIdSelector."""
        g = Graph.from_vertices('user_1', 'user_2', 'admin_1')

        sel = VertexIdSelector('user_*')
        matches = g.select_vertices(sel)

        assert len(matches) == 2

    def test_vertex_attrs_selector(self):
        """Test VertexAttrsSelector."""
        g = (Graph.builder()
             .add_vertex('A', age=30, city='NYC')
             .add_vertex('B', age=25, city='LA')
             .add_vertex('C', age=35, city='NYC')
             .build())

        sel = vertex.attrs(city='NYC')
        matches = g.select_vertices(sel)

        assert len(matches) == 2

    def test_vertex_attrs_selector_with_callable(self):
        """Test VertexAttrsSelector with callable."""
        g = (Graph.builder()
             .add_vertex('A', age=30)
             .add_vertex('B', age=25)
             .add_vertex('C', age=35)
             .build())

        sel = vertex.attrs(age=lambda a: a > 27)
        matches = g.select_vertices(sel)

        assert len(matches) == 2

    def test_vertex_degree_selector(self):
        """Test VertexDegreeSelector."""
        g = (Graph.builder()
             .add_star('center', 'A', 'B', 'C')
             .build())

        sel = vertex.degree(min_degree=3)
        matches = g.select_vertices(sel)

        assert len(matches) == 1
        assert any(v.id == 'center' for v in matches)

    def test_edge_weight_selector(self):
        """Test EdgeWeightSelector."""
        g = (Graph.builder()
             .add_edge('A', 'B', weight=5)
             .add_edge('B', 'C', weight=10)
             .add_edge('C', 'D', weight=3)
             .build())

        sel = edge.weight(min_weight=5)
        matches = g.select_edges(sel)

        assert len(matches) == 2

    def test_edge_directed_selector(self):
        """Test EdgeDirectedSelector."""
        g = (Graph.builder()
             .add_edge('A', 'B', directed=True)
             .add_edge('B', 'C', directed=False)
             .build())

        sel = edge.directed(False)
        matches = g.select_edges(sel)

        assert len(matches) == 1

    def test_selector_and_combinator(self):
        """Test AND combinator for selectors."""
        g = (Graph.builder()
             .add_vertex('A', age=30, city='NYC')
             .add_vertex('B', age=25, city='NYC')
             .add_vertex('C', age=35, city='LA')
             .build())

        sel = vertex.attrs(city='NYC') & vertex.attrs(age=lambda a: a > 27)
        matches = g.select_vertices(sel)

        assert len(matches) == 1
        assert any(v.id == 'A' for v in matches)

    def test_selector_or_combinator(self):
        """Test OR combinator for selectors."""
        g = (Graph.builder()
             .add_vertex('A', age=30)
             .add_vertex('B', age=25)
             .add_vertex('C', age=35)
             .build())

        sel = vertex.attrs(age=25) | vertex.attrs(age=35)
        matches = g.select_vertices(sel)

        assert len(matches) == 2

    def test_selector_not_combinator(self):
        """Test NOT combinator for selectors."""
        g = (Graph.builder()
             .add_vertex('A', active=True)
             .add_vertex('B', active=False)
             .add_vertex('C', active=True)
             .build())

        sel = ~vertex.attrs(active=True)
        matches = g.select_vertices(sel)

        assert len(matches) == 1
        assert any(v.id == 'B' for v in matches)

    def test_complex_selector_composition(self):
        """Test complex selector composition."""
        g = (Graph.builder()
             .add_vertex('A', age=30, city='NYC', active=True)
             .add_vertex('B', age=25, city='NYC', active=False)
             .add_vertex('C', age=35, city='LA', active=True)
             .add_vertex('D', age=40, city='NYC', active=True)
             .build())

        # Active NYC residents over 27
        sel = (vertex.attrs(city='NYC') &
               vertex.attrs(active=True) &
               vertex.attrs(age=lambda a: a > 27))
        matches = g.select_vertices(sel)

        assert len(matches) == 2  # A and D

    def test_selector_integration_with_transformer(self):
        """Test selector with transformer pipeline."""
        g = (Graph.builder()
             .add_vertex('A', value=10)
             .add_vertex('B', value=20)
             .add_vertex('C', value=30)
             .add_edge('A', 'B')
             .add_edge('B', 'C')
             .build())

        # Select high-value vertices, then convert to dict
        sel = vertex.attrs(value=lambda v: v > 15)
        high_value = g.select_vertices(sel)
        ids = {v.id for v in high_value}

        result = g | subgraph(ids) | to_dict()

        assert len(result['vertices']) == 2


class TestGraphViews:
    """Tests for lazy graph views."""

    def test_filtered_view_basic(self):
        """Test basic filtered view."""
        g = (Graph.builder()
             .add_vertex('A', active=True)
             .add_vertex('B', active=False)
             .add_vertex('C', active=True)
             .add_edge('A', 'B')
             .add_edge('B', 'C')
             .build())

        view = FilteredView(g, vertex_filter=lambda v: v.get('active'))

        assert view.vertex_count == 2
        assert view.edge_count == 0  # No edges between active vertices

    def test_filtered_view_lazy_iteration(self):
        """Test lazy iteration in filtered view."""
        g = Graph.from_vertices('A', 'B', 'C', 'D')

        view = FilteredView(g, vertex_filter=lambda v: v.id in {'A', 'B'})

        # Should iterate lazily without materializing
        count = 0
        for v in view.vertices():
            count += 1

        assert count == 2

    def test_filtered_view_materialize(self):
        """Test materializing view to graph."""
        g = (Graph.builder()
             .add_vertex('A', active=True)
             .add_vertex('B', active=False)
             .add_vertex('C', active=True)
             .add_edge('A', 'C', directed=False)
             .build())

        view = FilteredView(g, vertex_filter=lambda v: v.get('active'))
        materialized = view.materialize()

        assert isinstance(materialized, Graph)
        assert materialized.vertex_count == 2
        assert materialized.edge_count == 1

    def test_subgraph_view(self):
        """Test subgraph view."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'D'))

        view = SubGraphView(g, {'A', 'B', 'C'})

        assert view.vertex_count == 3
        assert view.edge_count == 2

    def test_reversed_view(self):
        """Test reversed view."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'))

        view = ReversedView(g)

        edges = list(view.edges())
        assert len(edges) == 2
        assert all(e.source == 'B' and e.target == 'A' or
                  e.source == 'C' and e.target == 'B'
                  for e in edges)

    def test_undirected_view(self):
        """Test undirected view."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'))

        view = UndirectedView(g)

        edges = list(view.edges())
        assert all(not e.directed for e in edges)

    def test_neighborhood_view(self):
        """Test neighborhood view."""
        g = (Graph.builder()
             .add_path('A', 'B', 'C', 'D', 'E', directed=False)
             .build())

        view = NeighborhoodView(g, 'C', k=1)

        # 1-hop neighborhood of C: B, C, D
        assert view.vertex_count == 3

    def test_neighborhood_view_multi_hop(self):
        """Test multi-hop neighborhood view."""
        g = (Graph.builder()
             .add_path('A', 'B', 'C', 'D', 'E', directed=False)
             .build())

        view = NeighborhoodView(g, 'C', k=2)

        # 2-hop neighborhood of C: A, B, C, D, E
        assert view.vertex_count == 5

    def test_view_convenience_functions(self):
        """Test convenience functions for creating views."""
        g = Graph.from_vertices('A', 'B', 'C')

        view1 = filtered_view(g, vertex_filter=lambda v: v.id != 'C')
        assert view1.vertex_count == 2

        view2 = subgraph_view(g, {'A', 'B'})
        assert view2.vertex_count == 2


class TestEdgeCases:
    """Tests for edge cases across Phase 3 features."""

    def test_transformer_empty_graph(self):
        """Test transformers on empty graph."""
        g = Graph()

        result = g | filter_vertices(lambda v: True) | to_dict()

        assert len(result['vertices']) == 0
        assert len(result['edges']) == 0

    def test_selector_no_matches(self):
        """Test selector with no matches."""
        g = Graph.from_vertices('A', 'B', 'C')

        sel = vertex.attrs(nonexistent=True)
        matches = g.select_vertices(sel)

        assert len(matches) == 0

    def test_view_empty_filter(self):
        """Test view with filter that matches nothing."""
        g = Graph.from_vertices('A', 'B', 'C')

        view = FilteredView(g, vertex_filter=lambda v: False)

        assert view.vertex_count == 0

    def test_pipeline_with_conditional(self):
        """Test conditional transformer in pipeline."""
        g = Graph.from_vertices('A', 'B')

        transform = filter_vertices(lambda v: v.id == 'A').when(lambda g: g.vertex_count > 1)
        result = g | transform

        assert result.vertex_count == 1  # Condition met, filter applied

    def test_selector_type_checking(self):
        """Test selector type checking in Graph methods."""
        g = Graph.from_vertices('A')

        with pytest.raises(TypeError):
            g.select_vertices("not a selector")

        with pytest.raises(TypeError):
            g.select_edges("not a selector")


class TestIntegration:
    """Integration tests combining multiple Phase 3 features."""

    def test_full_pipeline_workflow(self):
        """Test complete workflow with transformers, selectors, and views."""
        # Build graph
        g = (Graph.builder()
             .add_vertex('A', value=10, active=True)
             .add_vertex('B', value=20, active=False)
             .add_vertex('C', value=30, active=True)
             .add_vertex('D', value=40, active=True)
             .add_edge('A', 'B', weight=5)
             .add_edge('B', 'C', weight=15)
             .add_edge('C', 'D', weight=25)
             .build())

        # Use selector to find active vertices
        active_sel = vertex.attrs(active=True)
        active_ids = {v.id for v in g.select_vertices(active_sel)}

        # Create view of active subgraph
        view = subgraph_view(g, active_ids)

        # Transform view to graph and compute stats
        result = view.materialize() | stats()

        assert result['vertex_count'] == 3
        assert result['edge_count'] == 1  # Only C-D edge

    def test_chained_selectors_and_transformers(self):
        """Test chaining selectors with transformers."""
        g = (Graph.builder()
             .add_vertex('A', score=10)
             .add_vertex('B', score=20)
             .add_vertex('C', score=30)
             .add_edge('A', 'B')
             .add_edge('B', 'C')
             .build())

        # Select high-score vertices using selector
        high_score = vertex.attrs(score=lambda s: s >= 20)
        ids = {v.id for v in g.select_vertices(high_score)}

        # Extract subgraph and compute adjacency list
        result = g | subgraph(ids) | to_adjacency_list()

        assert 'B' in result
        assert 'C' in result['B']
