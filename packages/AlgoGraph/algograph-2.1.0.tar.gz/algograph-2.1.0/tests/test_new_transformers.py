"""
Tests for new transformers added in v2.0.0:
- UnionTransformer
- IntersectionTransformer
- DifferenceTransformer
- SortVerticesTransformer
- SortEdgesTransformer
- GroupByTransformer
- PartitionTransformer
- TopNTransformer
"""

import pytest
from AlgoGraph import Graph, Vertex, Edge
from AlgoGraph.transformers import (
    union, intersection, difference,
    sort_vertices, sort_edges,
    group_by, partition, top_n,
    UnionTransformer, IntersectionTransformer, DifferenceTransformer,
    SortVerticesTransformer, SortEdgesTransformer,
    GroupByTransformer, PartitionTransformer, TopNTransformer
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def graph1():
    """First test graph: A -> B -> C"""
    return Graph(
        vertices={
            Vertex('A', attrs={'score': 10, 'region': 'US'}),
            Vertex('B', attrs={'score': 20, 'region': 'EU'}),
            Vertex('C', attrs={'score': 30, 'region': 'US'}),
        },
        edges={
            Edge('A', 'B', weight=1.0),
            Edge('B', 'C', weight=2.0),
        }
    )


@pytest.fixture
def graph2():
    """Second test graph: B -> C -> D"""
    return Graph(
        vertices={
            Vertex('B', attrs={'score': 25, 'region': 'EU'}),
            Vertex('C', attrs={'score': 35, 'region': 'US'}),
            Vertex('D', attrs={'score': 40, 'region': 'ASIA'}),
        },
        edges={
            Edge('B', 'C', weight=3.0),
            Edge('C', 'D', weight=4.0),
        }
    )


@pytest.fixture
def graph3():
    """Third test graph with different structure: X -> Y"""
    return Graph(
        vertices={
            Vertex('X', attrs={'score': 100}),
            Vertex('Y', attrs={'score': 200}),
        },
        edges={
            Edge('X', 'Y', weight=10.0),
        }
    )


@pytest.fixture
def weighted_graph():
    """Graph with varied weights for sorting tests."""
    return Graph(
        vertices={
            Vertex('A', attrs={'score': 50}),
            Vertex('B', attrs={'score': 30}),
            Vertex('C', attrs={'score': 70}),
            Vertex('D', attrs={'score': 10}),
        },
        edges={
            Edge('A', 'B', weight=5.0),
            Edge('B', 'C', weight=2.0),
            Edge('C', 'D', weight=8.0),
            Edge('A', 'D', weight=1.0),
        }
    )


@pytest.fixture
def regional_graph():
    """Graph with regional attributes for grouping tests."""
    return Graph(
        vertices={
            Vertex('Alice', attrs={'region': 'US', 'active': True, 'score': 80}),
            Vertex('Bob', attrs={'region': 'US', 'active': False, 'score': 60}),
            Vertex('Charlie', attrs={'region': 'EU', 'active': True, 'score': 90}),
            Vertex('Diana', attrs={'region': 'EU', 'active': True, 'score': 70}),
            Vertex('Eve', attrs={'region': 'ASIA', 'active': False, 'score': 50}),
        },
        edges={
            Edge('Alice', 'Bob', weight=1.0),
            Edge('Charlie', 'Diana', weight=2.0),
        }
    )


# ============================================================================
# Union Tests
# ============================================================================

class TestUnionTransformer:
    """Tests for UnionTransformer."""

    def test_union_disjoint_graphs(self, graph1, graph3):
        """Union of disjoint graphs combines all vertices and edges."""
        result = graph1 | union(graph3)

        assert result.vertex_count == 5  # A, B, C, X, Y
        assert result.edge_count == 3  # A->B, B->C, X->Y

    def test_union_overlapping_graphs(self, graph1, graph2):
        """Union of overlapping graphs deduplicates by ID (first graph wins)."""
        result = graph1 | union(graph2)

        # Vertices: graph1 has A,B,C, graph2 has B,C,D
        # B and C are deduplicated by ID, keeping graph1's versions
        assert result.vertex_count == 4  # A, B, C, D (deduplicated by ID)

        # All unique vertex IDs present
        vertex_ids = {v.id for v in result.vertices}
        assert vertex_ids == {'A', 'B', 'C', 'D'}

        # Verify graph1's vertices are kept (not graph2's)
        b_vertex = next(v for v in result.vertices if v.id == 'B')
        assert b_vertex.get('score') == 20  # graph1's B, not graph2's B (25)

    def test_union_with_empty_graph(self, graph1):
        """Union with empty graph returns original graph."""
        empty = Graph(vertices=set(), edges=set())
        result = graph1 | union(empty)

        assert result.vertex_count == graph1.vertex_count
        assert result.edge_count == graph1.edge_count

    def test_union_factory_function(self, graph1, graph2):
        """Factory function creates UnionTransformer."""
        transformer = union(graph2)
        assert isinstance(transformer, UnionTransformer)

    def test_union_repr(self, graph1):
        """UnionTransformer has useful repr."""
        transformer = UnionTransformer(graph1)
        assert 'UnionTransformer' in repr(transformer)


# ============================================================================
# Intersection Tests
# ============================================================================

class TestIntersectionTransformer:
    """Tests for IntersectionTransformer."""

    def test_intersection_overlapping_graphs(self, graph1, graph2):
        """Intersection keeps only common vertices and edges."""
        result = graph1 | intersection(graph2)

        # Common vertices: B, C
        assert result.vertex_count == 2
        vertex_ids = {v.id for v in result.vertices}
        assert vertex_ids == {'B', 'C'}

        # Common edge: B->C (present in both)
        assert result.edge_count == 1

    def test_intersection_disjoint_graphs(self, graph1, graph3):
        """Intersection of disjoint graphs is empty."""
        result = graph1 | intersection(graph3)

        assert result.vertex_count == 0
        assert result.edge_count == 0

    def test_intersection_same_graph(self, graph1):
        """Intersection of graph with itself returns same structure."""
        result = graph1 | intersection(graph1)

        assert result.vertex_count == graph1.vertex_count
        assert result.edge_count == graph1.edge_count

    def test_intersection_factory_function(self, graph2):
        """Factory function creates IntersectionTransformer."""
        transformer = intersection(graph2)
        assert isinstance(transformer, IntersectionTransformer)

    def test_intersection_repr(self, graph1):
        """IntersectionTransformer has useful repr."""
        transformer = IntersectionTransformer(graph1)
        assert 'IntersectionTransformer' in repr(transformer)


# ============================================================================
# Difference Tests
# ============================================================================

class TestDifferenceTransformer:
    """Tests for DifferenceTransformer."""

    def test_difference_overlapping_graphs(self, graph1, graph2):
        """Difference removes common vertices."""
        result = graph1 | difference(graph2)

        # A is in graph1 but not graph2
        assert result.vertex_count == 1
        vertex_ids = {v.id for v in result.vertices}
        assert vertex_ids == {'A'}

        # No edges (A's edges connect to B which was removed)
        assert result.edge_count == 0

    def test_difference_disjoint_graphs(self, graph1, graph3):
        """Difference of disjoint graphs returns original."""
        result = graph1 | difference(graph3)

        assert result.vertex_count == graph1.vertex_count
        assert result.edge_count == graph1.edge_count

    def test_difference_same_graph(self, graph1):
        """Difference of graph with itself is empty."""
        result = graph1 | difference(graph1)

        assert result.vertex_count == 0
        assert result.edge_count == 0

    def test_difference_with_empty_graph(self, graph1):
        """Difference with empty graph returns original."""
        empty = Graph(vertices=set(), edges=set())
        result = graph1 | difference(empty)

        assert result.vertex_count == graph1.vertex_count

    def test_difference_factory_function(self, graph2):
        """Factory function creates DifferenceTransformer."""
        transformer = difference(graph2)
        assert isinstance(transformer, DifferenceTransformer)

    def test_difference_repr(self, graph1):
        """DifferenceTransformer has useful repr."""
        transformer = DifferenceTransformer(graph1)
        assert 'DifferenceTransformer' in repr(transformer)


# ============================================================================
# Sort Vertices Tests
# ============================================================================

class TestSortVerticesTransformer:
    """Tests for SortVerticesTransformer."""

    def test_sort_vertices_by_id(self, weighted_graph):
        """Default sort is by vertex ID."""
        result = weighted_graph | sort_vertices()

        ids = [v.id for v in result]
        assert ids == ['A', 'B', 'C', 'D']

    def test_sort_vertices_by_attribute(self, weighted_graph):
        """Sort vertices by custom attribute."""
        result = weighted_graph | sort_vertices(key=lambda v: v.get('score'))

        ids = [v.id for v in result]
        assert ids == ['D', 'B', 'A', 'C']  # 10, 30, 50, 70

    def test_sort_vertices_reverse(self, weighted_graph):
        """Sort vertices in descending order."""
        result = weighted_graph | sort_vertices(
            key=lambda v: v.get('score'),
            reverse=True
        )

        ids = [v.id for v in result]
        assert ids == ['C', 'A', 'B', 'D']  # 70, 50, 30, 10

    def test_sort_vertices_returns_list(self, weighted_graph):
        """Sort returns a list, not a Graph."""
        result = weighted_graph | sort_vertices()

        assert isinstance(result, list)
        assert all(isinstance(v, Vertex) for v in result)

    def test_sort_vertices_factory_function(self):
        """Factory function creates SortVerticesTransformer."""
        transformer = sort_vertices()
        assert isinstance(transformer, SortVerticesTransformer)

    def test_sort_vertices_repr(self):
        """SortVerticesTransformer has useful repr."""
        transformer = SortVerticesTransformer(reverse=True)
        assert 'SortVerticesTransformer' in repr(transformer)
        assert 'reverse=True' in repr(transformer)


# ============================================================================
# Sort Edges Tests
# ============================================================================

class TestSortEdgesTransformer:
    """Tests for SortEdgesTransformer."""

    def test_sort_edges_by_weight(self, weighted_graph):
        """Default sort is by edge weight."""
        result = weighted_graph | sort_edges()

        weights = [e.weight for e in result]
        assert weights == [1.0, 2.0, 5.0, 8.0]

    def test_sort_edges_by_custom_key(self, weighted_graph):
        """Sort edges by custom key function."""
        result = weighted_graph | sort_edges(key=lambda e: e.source)

        sources = [e.source for e in result]
        assert sources == ['A', 'A', 'B', 'C']

    def test_sort_edges_reverse(self, weighted_graph):
        """Sort edges in descending order."""
        result = weighted_graph | sort_edges(reverse=True)

        weights = [e.weight for e in result]
        assert weights == [8.0, 5.0, 2.0, 1.0]

    def test_sort_edges_returns_list(self, weighted_graph):
        """Sort returns a list, not a Graph."""
        result = weighted_graph | sort_edges()

        assert isinstance(result, list)
        assert all(isinstance(e, Edge) for e in result)

    def test_sort_edges_factory_function(self):
        """Factory function creates SortEdgesTransformer."""
        transformer = sort_edges()
        assert isinstance(transformer, SortEdgesTransformer)

    def test_sort_edges_repr(self):
        """SortEdgesTransformer has useful repr."""
        transformer = SortEdgesTransformer(reverse=True)
        assert 'SortEdgesTransformer' in repr(transformer)


# ============================================================================
# Group By Tests
# ============================================================================

class TestGroupByTransformer:
    """Tests for GroupByTransformer."""

    def test_group_by_region(self, regional_graph):
        """Group vertices by region attribute."""
        result = regional_graph | group_by(key=lambda v: v.get('region'))

        assert len(result) == 3  # US, EU, ASIA
        assert 'US' in result
        assert 'EU' in result
        assert 'ASIA' in result

        # US has Alice and Bob
        assert result['US'].vertex_count == 2

        # EU has Charlie and Diana with connecting edge
        assert result['EU'].vertex_count == 2
        assert result['EU'].edge_count == 1

        # ASIA has only Eve
        assert result['ASIA'].vertex_count == 1

    def test_group_by_boolean(self, regional_graph):
        """Group vertices by boolean attribute."""
        result = regional_graph | group_by(key=lambda v: v.get('active'))

        assert len(result) == 2
        assert True in result
        assert False in result

        # Active: Alice, Charlie, Diana
        assert result[True].vertex_count == 3

        # Inactive: Bob, Eve
        assert result[False].vertex_count == 2

    def test_group_by_preserves_edges(self, regional_graph):
        """Group preserves edges within groups."""
        result = regional_graph | group_by(key=lambda v: v.get('region'))

        # US group has edge Alice -> Bob
        us_edges = list(result['US'].edges)
        assert len(us_edges) == 1
        assert us_edges[0].source == 'Alice'
        assert us_edges[0].target == 'Bob'

    def test_group_by_factory_function(self):
        """Factory function creates GroupByTransformer."""
        transformer = group_by(key=lambda v: v.get('type'))
        assert isinstance(transformer, GroupByTransformer)

    def test_group_by_repr(self):
        """GroupByTransformer has useful repr."""
        transformer = GroupByTransformer(key=lambda v: v.id)
        assert 'GroupByTransformer' in repr(transformer)


# ============================================================================
# Partition Tests
# ============================================================================

class TestPartitionTransformer:
    """Tests for PartitionTransformer."""

    def test_partition_by_region(self, regional_graph):
        """Partition graph by region predicate."""
        us, non_us = regional_graph | partition(
            predicate=lambda v: v.get('region') == 'US'
        )

        # US partition
        assert us.vertex_count == 2
        us_ids = {v.id for v in us.vertices}
        assert us_ids == {'Alice', 'Bob'}

        # Non-US partition
        assert non_us.vertex_count == 3
        non_us_ids = {v.id for v in non_us.vertices}
        assert non_us_ids == {'Charlie', 'Diana', 'Eve'}

    def test_partition_by_active(self, regional_graph):
        """Partition graph by active status."""
        active, inactive = regional_graph | partition(
            predicate=lambda v: v.get('active')
        )

        assert active.vertex_count == 3  # Alice, Charlie, Diana
        assert inactive.vertex_count == 2  # Bob, Eve

    def test_partition_preserves_edges(self, regional_graph):
        """Partition preserves edges within partitions."""
        us, non_us = regional_graph | partition(
            predicate=lambda v: v.get('region') == 'US'
        )

        # US partition has Alice -> Bob edge
        assert us.edge_count == 1

        # Non-US partition has Charlie -> Diana edge
        assert non_us.edge_count == 1

    def test_partition_all_match(self, regional_graph):
        """Partition where all vertices match."""
        all_verts, none_verts = regional_graph | partition(
            predicate=lambda v: True
        )

        assert all_verts.vertex_count == 5
        assert none_verts.vertex_count == 0

    def test_partition_none_match(self, regional_graph):
        """Partition where no vertices match."""
        none_verts, all_verts = regional_graph | partition(
            predicate=lambda v: False
        )

        assert none_verts.vertex_count == 0
        assert all_verts.vertex_count == 5

    def test_partition_factory_function(self):
        """Factory function creates PartitionTransformer."""
        transformer = partition(predicate=lambda v: v.get('active'))
        assert isinstance(transformer, PartitionTransformer)

    def test_partition_repr(self):
        """PartitionTransformer has useful repr."""
        transformer = PartitionTransformer(predicate=lambda v: True)
        assert 'PartitionTransformer' in repr(transformer)


# ============================================================================
# Top N Tests
# ============================================================================

class TestTopNTransformer:
    """Tests for TopNTransformer."""

    def test_top_n_by_score(self, regional_graph):
        """Get top N vertices by score."""
        result = regional_graph | top_n(n=2, key=lambda v: v.get('score'))

        assert result.vertex_count == 2
        ids = {v.id for v in result.vertices}
        # Charlie (90) and Alice (80) have highest scores
        assert ids == {'Charlie', 'Alice'}

    def test_top_n_bottom(self, regional_graph):
        """Get bottom N vertices (reverse=False)."""
        result = regional_graph | top_n(
            n=2,
            key=lambda v: v.get('score'),
            reverse=False
        )

        assert result.vertex_count == 2
        ids = {v.id for v in result.vertices}
        # Eve (50) and Bob (60) have lowest scores
        assert ids == {'Eve', 'Bob'}

    def test_top_n_preserves_internal_edges(self, regional_graph):
        """Top N preserves edges between selected vertices."""
        result = regional_graph | top_n(n=3, key=lambda v: v.get('score'))

        # Top 3 by score: Charlie (90), Alice (80), Diana (70)
        ids = {v.id for v in result.vertices}
        assert ids == {'Charlie', 'Alice', 'Diana'}

        # Charlie -> Diana edge should be preserved
        assert result.edge_count == 1

    def test_top_n_larger_than_graph(self, graph1):
        """Top N where N >= vertex count returns all vertices."""
        result = graph1 | top_n(n=100, key=lambda v: v.get('score'))

        assert result.vertex_count == graph1.vertex_count

    def test_top_n_zero(self, regional_graph):
        """Top 0 returns empty graph."""
        result = regional_graph | top_n(n=0, key=lambda v: v.get('score'))

        assert result.vertex_count == 0
        assert result.edge_count == 0

    def test_top_n_factory_function(self):
        """Factory function creates TopNTransformer."""
        transformer = top_n(n=5, key=lambda v: v.id)
        assert isinstance(transformer, TopNTransformer)

    def test_top_n_repr(self):
        """TopNTransformer has useful repr."""
        transformer = TopNTransformer(n=5, key=lambda v: v.id, reverse=True)
        assert 'TopNTransformer' in repr(transformer)
        assert 'n=5' in repr(transformer)


# ============================================================================
# Integration Tests
# ============================================================================

class TestTransformerIntegration:
    """Integration tests for combining new transformers."""

    def test_union_then_group_by(self, graph1, graph2):
        """Combine union with group_by."""
        combined = graph1 | union(graph2)
        groups = combined | group_by(key=lambda v: v.get('region'))

        # Should have US, EU, ASIA regions
        assert 'US' in groups or 'EU' in groups

    def test_partition_then_top_n(self, regional_graph):
        """Partition then get top N from each partition."""
        active, inactive = regional_graph | partition(lambda v: v.get('active'))

        top_active = active | top_n(n=1, key=lambda v: v.get('score'))
        top_inactive = inactive | top_n(n=1, key=lambda v: v.get('score'))

        # Top active: Charlie (90)
        assert {v.id for v in top_active.vertices} == {'Charlie'}

        # Top inactive: Bob (60)
        assert {v.id for v in top_inactive.vertices} == {'Bob'}

    def test_difference_then_sort(self, graph1, graph2):
        """Compute difference then sort remaining vertices."""
        diff = graph1 | difference(graph2)
        sorted_verts = diff | sort_vertices(key=lambda v: v.get('score'))

        # Only A remains after difference
        assert len(sorted_verts) == 1
        assert sorted_verts[0].id == 'A'

    def test_intersection_then_partition(self, graph1, graph2):
        """Intersect then partition."""
        common = graph1 | intersection(graph2)
        # Common vertices are B and C

        eu, non_eu = common | partition(
            lambda v: v.get('region') == 'EU'
        )

        # B is EU, C is US
        assert eu.vertex_count == 1
        assert non_eu.vertex_count == 1

    def test_chained_set_operations(self, graph1, graph2, graph3):
        """Chain multiple set operations."""
        # (graph1 union graph2) difference graph3
        result = graph1 | union(graph2) | difference(graph3)

        # Union deduplicates by ID: A, B, C, D (4 vertices)
        # X and Y from graph3 don't overlap, difference removes nothing
        assert result.vertex_count == 4

        # All unique IDs present
        vertex_ids = {v.id for v in result.vertices}
        assert vertex_ids == {'A', 'B', 'C', 'D'}


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Edge case tests for new transformers."""

    def test_empty_graph_operations(self):
        """Operations on empty graphs."""
        empty = Graph(vertices=set(), edges=set())

        # Union with empty
        result = empty | union(empty)
        assert result.vertex_count == 0

        # Intersection of empty
        result = empty | intersection(empty)
        assert result.vertex_count == 0

        # Sort empty
        result = empty | sort_vertices()
        assert result == []

        # Group empty
        result = empty | group_by(lambda v: v.id)
        assert result == {}

    def test_single_vertex_graph(self):
        """Operations on single vertex graph."""
        single = Graph(
            vertices={Vertex('A', attrs={'score': 100})},
            edges=set()
        )

        # Union
        result = single | union(single)
        assert result.vertex_count == 1

        # Top N
        result = single | top_n(n=5, key=lambda v: v.get('score'))
        assert result.vertex_count == 1

        # Partition
        match, no_match = single | partition(lambda v: True)
        assert match.vertex_count == 1
        assert no_match.vertex_count == 0

    def test_none_attributes(self):
        """Handle vertices with None attributes."""
        graph = Graph(
            vertices={
                Vertex('A', attrs={'score': None}),
                Vertex('B', attrs={'score': 10}),
            },
            edges=set()
        )

        # Sort with None handling
        result = graph | sort_vertices(
            key=lambda v: v.get('score') or 0
        )
        ids = [v.id for v in result]
        assert 'A' in ids and 'B' in ids

    def test_missing_attributes(self):
        """Handle vertices with missing attributes."""
        graph = Graph(
            vertices={
                Vertex('A'),  # No score attribute
                Vertex('B', attrs={'score': 10}),
            },
            edges=set()
        )

        # Group by with default value
        result = graph | group_by(
            key=lambda v: v.get('score', 0)
        )
        assert 0 in result  # A goes here
        assert 10 in result  # B goes here
