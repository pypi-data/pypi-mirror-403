"""
Tests for the Query DSL module.
"""

import pytest
from AlgoGraph import Graph, Vertex, Edge
from AlgoGraph.query import (
    Query, query, VertexQuery, EdgeQuery, PathQuery,
    QueryResult, AggregateBuilder, Path
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def simple_graph():
    """Simple test graph: A -> B -> C -> D"""
    return Graph(
        vertices={
            Vertex('A', attrs={'score': 10, 'active': True, 'region': 'US'}),
            Vertex('B', attrs={'score': 20, 'active': True, 'region': 'EU'}),
            Vertex('C', attrs={'score': 30, 'active': False, 'region': 'US'}),
            Vertex('D', attrs={'score': 40, 'active': True, 'region': 'ASIA'}),
        },
        edges={
            Edge('A', 'B', weight=1.0),
            Edge('B', 'C', weight=2.0),
            Edge('C', 'D', weight=3.0),
        }
    )


@pytest.fixture
def complex_graph():
    """More complex graph with multiple paths."""
    return Graph(
        vertices={
            Vertex('A', attrs={'score': 100}),
            Vertex('B', attrs={'score': 200}),
            Vertex('C', attrs={'score': 150}),
            Vertex('D', attrs={'score': 300}),
            Vertex('E', attrs={'score': 50}),
        },
        edges={
            Edge('A', 'B', weight=1.0),
            Edge('A', 'C', weight=2.0),
            Edge('B', 'D', weight=3.0),
            Edge('C', 'D', weight=1.0),
            Edge('C', 'E', weight=4.0),
            Edge('E', 'D', weight=2.0),
        }
    )


@pytest.fixture
def social_graph():
    """Social network style graph."""
    return Graph(
        vertices={
            Vertex('Alice', attrs={'age': 30, 'city': 'NYC'}),
            Vertex('Bob', attrs={'age': 25, 'city': 'LA'}),
            Vertex('Carol', attrs={'age': 35, 'city': 'NYC'}),
            Vertex('Dave', attrs={'age': 28, 'city': 'Chicago'}),
            Vertex('Eve', attrs={'age': 22, 'city': 'LA'}),
        },
        edges={
            Edge('Alice', 'Bob', weight=1.0, attrs={'type': 'friend'}),
            Edge('Alice', 'Carol', weight=1.0, attrs={'type': 'colleague'}),
            Edge('Bob', 'Dave', weight=1.0, attrs={'type': 'friend'}),
            Edge('Carol', 'Dave', weight=1.0, attrs={'type': 'friend'}),
            Edge('Dave', 'Eve', weight=1.0, attrs={'type': 'family'}),
        }
    )


# ============================================================================
# Query Builder Tests
# ============================================================================

class TestQueryBuilder:
    """Tests for the main Query class."""

    def test_create_query(self, simple_graph):
        """Can create a query builder."""
        q = Query(simple_graph)
        assert q.graph == simple_graph

    def test_query_convenience_function(self, simple_graph):
        """query() function creates Query instance."""
        q = query(simple_graph)
        assert isinstance(q, Query)

    def test_get_vertex(self, simple_graph):
        """Can get a specific vertex."""
        q = Query(simple_graph)
        v = q.vertex('A')
        assert v is not None
        assert v.id == 'A'

    def test_get_nonexistent_vertex(self, simple_graph):
        """Getting nonexistent vertex returns None."""
        q = Query(simple_graph)
        v = q.vertex('X')
        assert v is None

    def test_get_edge(self, simple_graph):
        """Can get a specific edge."""
        q = Query(simple_graph)
        e = q.edge('A', 'B')
        assert e is not None
        assert e.source == 'A'
        assert e.target == 'B'

    def test_subgraph(self, simple_graph):
        """Can extract a subgraph."""
        q = Query(simple_graph)
        sub = q.subgraph({'A', 'B'})
        assert sub.vertex_count == 2
        assert sub.edge_count == 1


# ============================================================================
# Vertex Query Tests
# ============================================================================

class TestVertexQuery:
    """Tests for VertexQuery."""

    def test_select_all(self, simple_graph):
        """Select all vertices."""
        result = Query(simple_graph).vertices().select()
        assert len(result) == 4

    def test_where_predicate(self, simple_graph):
        """Filter with predicate."""
        result = (Query(simple_graph)
                  .vertices()
                  .where(lambda v: v.get('active'))
                  .select())
        assert len(result) == 3  # A, B, D are active

    def test_has_attribute(self, simple_graph):
        """Filter by attribute existence."""
        result = (Query(simple_graph)
                  .vertices()
                  .has('score')
                  .select())
        assert len(result) == 4

    def test_has_attribute_value(self, simple_graph):
        """Filter by attribute value."""
        result = (Query(simple_graph)
                  .vertices()
                  .has('region', 'US')
                  .select())
        assert len(result) == 2  # A, C

    def test_has_not(self, simple_graph):
        """Filter by attribute absence."""
        g = Graph(
            vertices={
                Vertex('A', attrs={'x': 1}),
                Vertex('B'),
            },
            edges=set()
        )
        result = Query(g).vertices().has_not('x').select()
        assert len(result) == 1
        assert result.first().id == 'B'

    def test_chained_where(self, simple_graph):
        """Multiple where clauses."""
        result = (Query(simple_graph)
                  .vertices()
                  .where(lambda v: v.get('active'))
                  .where(lambda v: v.get('score', 0) > 15)
                  .select())
        assert len(result) == 2  # B (20), D (40)

    def test_order_by(self, simple_graph):
        """Sort results."""
        result = (Query(simple_graph)
                  .vertices()
                  .order_by(lambda v: v.get('score'))
                  .select())
        ids = [v.id for v in result]
        assert ids == ['A', 'B', 'C', 'D']

    def test_order_by_reverse(self, simple_graph):
        """Sort results descending."""
        result = (Query(simple_graph)
                  .vertices()
                  .order_by(lambda v: v.get('score'), reverse=True)
                  .select())
        ids = [v.id for v in result]
        assert ids == ['D', 'C', 'B', 'A']

    def test_limit(self, simple_graph):
        """Limit results."""
        result = (Query(simple_graph)
                  .vertices()
                  .order_by(lambda v: v.get('score'), reverse=True)
                  .limit(2)
                  .select())
        assert len(result) == 2

    def test_offset(self, simple_graph):
        """Skip results."""
        result = (Query(simple_graph)
                  .vertices()
                  .order_by(lambda v: v.get('score'))
                  .offset(2)
                  .select())
        assert len(result) == 2
        ids = [v.id for v in result]
        assert ids == ['C', 'D']

    def test_limit_and_offset(self, simple_graph):
        """Pagination with limit and offset."""
        result = (Query(simple_graph)
                  .vertices()
                  .order_by(lambda v: v.get('score'))
                  .offset(1)
                  .limit(2)
                  .select())
        assert len(result) == 2
        ids = [v.id for v in result]
        assert ids == ['B', 'C']

    def test_count(self, simple_graph):
        """Count matching vertices."""
        count = (Query(simple_graph)
                 .vertices()
                 .where(lambda v: v.get('active'))
                 .count())
        assert count == 3

    def test_exists(self, simple_graph):
        """Check existence."""
        exists = (Query(simple_graph)
                  .vertices()
                  .has('region', 'US')
                  .exists())
        assert exists is True

    def test_not_exists(self, simple_graph):
        """Check non-existence."""
        exists = (Query(simple_graph)
                  .vertices()
                  .has('region', 'INVALID')
                  .exists())
        assert exists is False

    def test_neighbors_of(self, simple_graph):
        """Filter to neighbors."""
        result = (Query(simple_graph)
                  .vertices()
                  .neighbors_of('B')
                  .select())
        # B's neighbors are A (incoming) and C (outgoing)
        # But neighbors_of uses graph.neighbors which might only return outgoing
        ids = {v.id for v in result}
        assert 'C' in ids

    def test_degree_at_least(self, complex_graph):
        """Filter by minimum degree."""
        result = (Query(complex_graph)
                  .vertices()
                  .degree_at_least(2)
                  .select())
        # A has out-degree 2, C has out-degree 2, D has in-degree 3
        assert len(result) >= 2

    def test_reachable_from(self, simple_graph):
        """Filter to reachable vertices."""
        result = (Query(simple_graph)
                  .vertices()
                  .reachable_from('A')
                  .select())
        ids = {v.id for v in result}
        assert ids == {'A', 'B', 'C', 'D'}

    def test_reachable_from_with_depth(self, simple_graph):
        """Filter to reachable vertices with depth limit."""
        result = (Query(simple_graph)
                  .vertices()
                  .reachable_from('A', max_depth=1)
                  .select())
        ids = {v.id for v in result}
        assert ids == {'A', 'B'}


# ============================================================================
# Edge Query Tests
# ============================================================================

class TestEdgeQuery:
    """Tests for EdgeQuery."""

    def test_select_all(self, simple_graph):
        """Select all edges."""
        result = Query(simple_graph).edges().select()
        assert len(result) == 3

    def test_from_vertex(self, simple_graph):
        """Filter by source vertex."""
        result = (Query(simple_graph)
                  .edges()
                  .from_vertex('A')
                  .select())
        assert len(result) == 1
        assert result.first().target == 'B'

    def test_to_vertex(self, simple_graph):
        """Filter by target vertex."""
        result = (Query(simple_graph)
                  .edges()
                  .to_vertex('D')
                  .select())
        assert len(result) == 1
        assert result.first().source == 'C'

    def test_between(self, simple_graph):
        """Filter edges between vertices."""
        result = (Query(simple_graph)
                  .edges()
                  .between('A', 'B')
                  .select())
        assert len(result) == 1

    def test_weight_at_least(self, simple_graph):
        """Filter by minimum weight."""
        result = (Query(simple_graph)
                  .edges()
                  .weight_at_least(2.0)
                  .select())
        assert len(result) == 2  # B->C (2.0), C->D (3.0)

    def test_weight_at_most(self, simple_graph):
        """Filter by maximum weight."""
        result = (Query(simple_graph)
                  .edges()
                  .weight_at_most(2.0)
                  .select())
        assert len(result) == 2  # A->B (1.0), B->C (2.0)

    def test_weight_between(self, simple_graph):
        """Filter by weight range."""
        result = (Query(simple_graph)
                  .edges()
                  .weight_between(1.5, 2.5)
                  .select())
        assert len(result) == 1  # B->C (2.0)

    def test_order_by_weight(self, simple_graph):
        """Sort by weight."""
        result = (Query(simple_graph)
                  .edges()
                  .order_by_weight()
                  .select())
        weights = [e.weight for e in result]
        assert weights == [1.0, 2.0, 3.0]

    def test_total_weight(self, simple_graph):
        """Sum of edge weights."""
        total = (Query(simple_graph)
                 .edges()
                 .total_weight())
        assert total == 6.0  # 1 + 2 + 3

    def test_has_attribute(self, social_graph):
        """Filter edges by attribute."""
        result = (Query(social_graph)
                  .edges()
                  .has('type', 'friend')
                  .select())
        assert len(result) == 3


# ============================================================================
# Path Query Tests
# ============================================================================

class TestPathQuery:
    """Tests for PathQuery."""

    def test_find_shortest(self, simple_graph):
        """Find shortest path."""
        path = (Query(simple_graph)
                .paths()
                .from_vertex('A')
                .to_vertex('D')
                .find_shortest())

        assert path is not None
        assert path.start == 'A'
        assert path.end == 'D'
        assert path.length == 3

    def test_no_path(self, simple_graph):
        """No path exists."""
        path = (Query(simple_graph)
                .paths()
                .from_vertex('D')
                .to_vertex('A')
                .find_shortest())

        assert path is None

    def test_path_to_self(self, simple_graph):
        """Path to self."""
        path = (Query(simple_graph)
                .paths()
                .from_vertex('A')
                .to_vertex('A')
                .find_shortest())

        assert path is not None
        assert path.length == 0

    def test_find_all_paths(self, complex_graph):
        """Find all paths."""
        paths = (Query(complex_graph)
                 .paths()
                 .from_vertex('A')
                 .to_vertex('D')
                 .find_all())

        assert len(paths) >= 2  # Multiple paths exist

    def test_max_length(self, complex_graph):
        """Limit path length."""
        paths = (Query(complex_graph)
                 .paths()
                 .from_vertex('A')
                 .to_vertex('D')
                 .max_length(2)
                 .find_all())

        for path in paths:
            assert path.length <= 2

    def test_min_length(self, complex_graph):
        """Require minimum length."""
        paths = (Query(complex_graph)
                 .paths()
                 .from_vertex('A')
                 .to_vertex('D')
                 .min_length(3)
                 .find_all())

        for path in paths:
            assert path.length >= 3

    def test_avoiding_vertices(self, complex_graph):
        """Avoid specific vertices."""
        paths = (Query(complex_graph)
                 .paths()
                 .from_vertex('A')
                 .to_vertex('D')
                 .avoiding('B')
                 .find_all())

        for path in paths:
            assert 'B' not in path.vertices

    def test_through_vertex(self, complex_graph):
        """Require path through vertex."""
        paths = (Query(complex_graph)
                 .paths()
                 .from_vertex('A')
                 .to_vertex('D')
                 .through('C')
                 .find_all())

        for path in paths:
            assert 'C' in path.vertices

    def test_path_exists(self, simple_graph):
        """Check if path exists."""
        exists = (Query(simple_graph)
                  .paths()
                  .from_vertex('A')
                  .to_vertex('D')
                  .exists())
        assert exists is True

    def test_path_total_weight(self, simple_graph):
        """Path total weight."""
        path = (Query(simple_graph)
                .paths()
                .from_vertex('A')
                .to_vertex('D')
                .find_shortest())

        assert path.total_weight == 6.0  # 1 + 2 + 3


# ============================================================================
# QueryResult Tests
# ============================================================================

class TestQueryResult:
    """Tests for QueryResult."""

    def test_iteration(self, simple_graph):
        """Can iterate over results."""
        result = Query(simple_graph).vertices().select()
        ids = [v.id for v in result]
        assert len(ids) == 4

    def test_len(self, simple_graph):
        """len() works."""
        result = Query(simple_graph).vertices().select()
        assert len(result) == 4

    def test_bool(self, simple_graph):
        """bool conversion."""
        result = Query(simple_graph).vertices().select()
        assert bool(result) is True

        empty = Query(simple_graph).vertices().has('x', 'invalid').select()
        assert bool(empty) is False

    def test_first(self, simple_graph):
        """Get first result."""
        result = (Query(simple_graph)
                  .vertices()
                  .order_by(lambda v: v.id)
                  .select())
        assert result.first().id == 'A'

    def test_first_empty(self, simple_graph):
        """First on empty result."""
        result = Query(simple_graph).vertices().has('x', 'invalid').select()
        assert result.first() is None

    def test_to_list(self, simple_graph):
        """Convert to list."""
        result = Query(simple_graph).vertices().select()
        lst = result.to_list()
        assert isinstance(lst, list)
        assert len(lst) == 4

    def test_to_set(self, simple_graph):
        """Convert to set."""
        result = Query(simple_graph).vertices().select()
        s = result.to_set()
        assert isinstance(s, set)
        assert len(s) == 4

    def test_ids(self, simple_graph):
        """Get IDs from results."""
        result = Query(simple_graph).vertices().select()
        ids = result.ids()
        assert set(ids) == {'A', 'B', 'C', 'D'}

    def test_to_subgraph(self, simple_graph):
        """Convert to subgraph."""
        result = (Query(simple_graph)
                  .vertices()
                  .has('region', 'US')
                  .select())
        sub = result.to_subgraph()
        assert sub.vertex_count == 2


# ============================================================================
# Aggregate Tests
# ============================================================================

class TestAggregate:
    """Tests for AggregateBuilder."""

    def test_count(self, simple_graph):
        """Count aggregation."""
        result = (Query(simple_graph)
                  .vertices()
                  .aggregate()
                  .count()
                  .result())
        assert result['count'] == 4

    def test_sum(self, simple_graph):
        """Sum aggregation."""
        result = (Query(simple_graph)
                  .vertices()
                  .aggregate()
                  .sum('score')
                  .result())
        assert result['sum_score'] == 100  # 10+20+30+40

    def test_avg(self, simple_graph):
        """Average aggregation."""
        result = (Query(simple_graph)
                  .vertices()
                  .aggregate()
                  .avg('score')
                  .result())
        assert result['avg_score'] == 25.0  # 100/4

    def test_min_max(self, simple_graph):
        """Min/max aggregation."""
        result = (Query(simple_graph)
                  .vertices()
                  .aggregate()
                  .min('score')
                  .max('score')
                  .result())
        assert result['min_score'] == 10
        assert result['max_score'] == 40

    def test_group_by(self, simple_graph):
        """Group by aggregation."""
        groups = (Query(simple_graph)
                  .vertices()
                  .aggregate()
                  .group_by('region'))
        assert 'US' in groups
        assert 'EU' in groups
        assert len(groups['US']) == 2

    def test_chained_aggregates(self, simple_graph):
        """Multiple aggregations."""
        result = (Query(simple_graph)
                  .vertices()
                  .where(lambda v: v.get('active'))
                  .aggregate()
                  .count()
                  .sum('score')
                  .avg('score')
                  .result())

        assert result['count'] == 3
        assert result['sum_score'] == 70  # 10+20+40
        assert abs(result['avg_score'] - 23.33) < 0.1


# ============================================================================
# Integration Tests
# ============================================================================

class TestQueryIntegration:
    """Integration tests for complex queries."""

    def test_find_top_scorers_in_region(self, simple_graph):
        """Find top scorers in a region."""
        result = (Query(simple_graph)
                  .vertices()
                  .has('region', 'US')
                  .order_by(lambda v: v.get('score'), reverse=True)
                  .limit(1)
                  .select())

        assert result.first().id == 'C'  # Highest score in US

    def test_find_path_avoiding_inactive(self, simple_graph):
        """Find path avoiding inactive nodes."""
        # C is inactive
        path = (Query(simple_graph)
                .paths()
                .from_vertex('A')
                .to_vertex('D')
                .avoiding('C')
                .find_shortest())

        # No path exists avoiding C
        assert path is None

    def test_heavy_edges_between_active_vertices(self, simple_graph):
        """Find heavy edges between active vertices."""
        active_ids = {v.id for v in Query(simple_graph)
                      .vertices()
                      .where(lambda v: v.get('active'))
                      .select()}

        result = (Query(simple_graph)
                  .edges()
                  .where(lambda e: e.source in active_ids and e.target in active_ids)
                  .weight_at_least(1.0)
                  .select())

        # Only A->B is between two active vertices
        assert len(result) == 1

    def test_neighbors_query(self, social_graph):
        """Query using neighbors convenience method."""
        result = Query(social_graph).neighbors('Alice', depth=1)
        ids = {v.id for v in result}
        assert 'Bob' in ids
        assert 'Carol' in ids


# ============================================================================
# Path Object Tests
# ============================================================================

class TestPath:
    """Tests for Path dataclass."""

    def test_path_properties(self):
        """Path has correct properties."""
        path = Path(
            vertices=['A', 'B', 'C'],
            edges=[
                Edge('A', 'B', weight=1.0),
                Edge('B', 'C', weight=2.0)
            ]
        )

        assert path.length == 2
        assert path.total_weight == 3.0
        assert path.start == 'A'
        assert path.end == 'C'

    def test_path_repr(self):
        """Path has useful repr."""
        path = Path(vertices=['A', 'B', 'C'], edges=[])
        assert 'A -> B -> C' in repr(path)
