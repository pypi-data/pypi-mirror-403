"""
Tests for Phase 2 algorithms (centrality, flow, matching, coloring).
"""

import pytest

from AlgoGraph import Vertex, Edge, Graph
from AlgoGraph.algorithms import (
    # Centrality
    pagerank, betweenness_centrality, closeness_centrality,
    degree_centrality, eigenvector_centrality,
    # Flow
    edmonds_karp, max_flow, min_cut, ford_fulkerson,
    # Matching
    hopcroft_karp, maximum_bipartite_matching, is_perfect_matching,
    maximum_matching, matching_size, is_maximal_matching,
    # Coloring
    greedy_coloring, welsh_powell, chromatic_number, is_valid_coloring,
    dsatur, edge_coloring, chromatic_index, is_k_colorable
)


class TestCentrality:
    """Tests for centrality algorithms."""

    def test_pagerank_simple(self):
        """Test PageRank on simple graph."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'A'))

        scores = pagerank(g)

        # All scores should sum to 1.0 (approximately)
        assert abs(sum(scores.values()) - 1.0) < 0.01

        # All vertices should have similar PageRank in this symmetric cycle
        assert all(0.3 < score < 0.4 for score in scores.values())

    def test_pagerank_empty(self):
        """Test PageRank on empty graph."""
        g = Graph()
        scores = pagerank(g)
        assert scores == {}

    def test_betweenness_centrality_bridge(self):
        """Test betweenness centrality identifies bridge vertex."""
        # Linear graph: A-B-C where B is the bridge
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), directed=False)

        bc = betweenness_centrality(g)

        # B should have highest betweenness (it's on all paths)
        assert bc['B'] > bc['A']
        assert bc['B'] > bc['C']

    def test_betweenness_centrality_star(self):
        """Test betweenness centrality on star graph."""
        # Star graph: center connected to A, B, C
        g = Graph.builder().add_star('center', 'A', 'B', 'C').build()

        bc = betweenness_centrality(g, normalized=False)

        # Center should have highest betweenness
        assert bc['center'] > bc['A']
        assert bc['A'] == bc['B'] == bc['C']  # Leaves have equal betweenness

    def test_closeness_centrality_star(self):
        """Test closeness centrality on star graph."""
        g = Graph.builder().add_star('center', 'A', 'B', 'C').build()

        cc = closeness_centrality(g)

        # Center should have highest closeness (closest to all)
        assert cc['center'] > cc['A']
        assert cc['center'] > cc['B']
        assert cc['center'] > cc['C']

    def test_closeness_centrality_path(self):
        """Test closeness centrality on path graph."""
        g = Graph.builder().add_path('A', 'B', 'C', 'D', 'E', directed=False).build()

        cc = closeness_centrality(g)

        # Middle vertex C should have highest closeness
        assert cc['C'] > cc['A']
        assert cc['C'] > cc['E']

    def test_degree_centrality(self):
        """Test degree centrality."""
        g = (Graph.builder()
             .add_edge('A', 'B', directed=False)
             .add_edge('A', 'C', directed=False)
             .add_edge('A', 'D', directed=False)
             .build())

        dc = degree_centrality(g, normalized=False)

        # A has degree 3, others have degree 1
        assert dc['A'] == 3.0
        assert dc['B'] == 1.0

    def test_degree_centrality_normalized(self):
        """Test normalized degree centrality."""
        g = Graph.builder().add_star('center', 'A', 'B', 'C').build()

        dc = degree_centrality(g, normalized=True)

        # All scores should be between 0 and 1
        assert all(0 <= score <= 1 for score in dc.values())

    def test_eigenvector_centrality(self):
        """Test eigenvector centrality."""
        # Triangle graph
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), ('C', 'A'), directed=False)

        ec = eigenvector_centrality(g)

        # All vertices should have similar importance in symmetric graph
        scores = list(ec.values())
        assert abs(scores[0] - scores[1]) < 0.1
        assert abs(scores[1] - scores[2]) < 0.1


class TestFlow:
    """Tests for flow network algorithms."""

    def test_edmonds_karp_simple(self):
        """Test Edmonds-Karp on simple flow network."""
        g = (Graph.builder()
             .add_edge('S', 'T', weight=10)
             .build())

        max_flow_value, flow = edmonds_karp(g, 'S', 'T')

        assert max_flow_value == 10.0

    def test_edmonds_karp_multiple_paths(self):
        """Test Edmonds-Karp with multiple paths."""
        # Two paths: S->A->T (10) and S->B->T (10)
        g = (Graph.builder()
             .add_edge('S', 'A', weight=10)
             .add_edge('S', 'B', weight=10)
             .add_edge('A', 'T', weight=10)
             .add_edge('B', 'T', weight=10)
             .build())

        max_flow_value, flow = edmonds_karp(g, 'S', 'T')

        assert max_flow_value == 20.0

    def test_edmonds_karp_bottleneck(self):
        """Test Edmonds-Karp with bottleneck."""
        # Path with bottleneck: S->A (100), A->T (5)
        g = (Graph.builder()
             .add_edge('S', 'A', weight=100)
             .add_edge('A', 'T', weight=5)
             .build())

        max_flow_value, flow = edmonds_karp(g, 'S', 'T')

        assert max_flow_value == 5.0

    def test_max_flow(self):
        """Test max_flow convenience function."""
        g = Graph.from_edges(('S', 'T'), weight=10)

        flow_value = max_flow(g, 'S', 'T')

        assert flow_value == 10.0

    def test_min_cut(self):
        """Test minimum cut."""
        g = (Graph.builder()
             .add_edge('S', 'A', weight=10)
             .add_edge('A', 'T', weight=5)
             .build())

        cut_value, source_set, sink_set = min_cut(g, 'S', 'T')

        # Cut value should equal max flow
        assert cut_value == 5.0

        # S and A should be in source set
        assert 'S' in source_set
        assert 'A' in source_set

        # T should be in sink set
        assert 'T' in sink_set

    def test_ford_fulkerson_bfs(self):
        """Test Ford-Fulkerson with BFS (Edmonds-Karp)."""
        g = Graph.from_edges(('S', 'T'), weight=10)

        max_flow_value, flow = ford_fulkerson(g, 'S', 'T', path_finder='bfs')

        assert max_flow_value == 10.0

    def test_edmonds_karp_invalid_source(self):
        """Test Edmonds-Karp with invalid source."""
        g = Graph.from_edges(('A', 'B'), weight=10)

        with pytest.raises(ValueError, match="Source.*not found"):
            edmonds_karp(g, 'X', 'B')

    def test_edmonds_karp_invalid_sink(self):
        """Test Edmonds-Karp with invalid sink."""
        g = Graph.from_edges(('A', 'B'), weight=10)

        with pytest.raises(ValueError, match="Sink.*not found"):
            edmonds_karp(g, 'A', 'X')


class TestMatching:
    """Tests for matching algorithms."""

    def test_hopcroft_karp_simple(self):
        """Test Hopcroft-Karp on simple bipartite graph."""
        g = (Graph.builder()
             .add_edge('A', 'X', directed=False)
             .add_edge('B', 'Y', directed=False)
             .build())

        left = {'A', 'B'}
        right = {'X', 'Y'}

        matching = hopcroft_karp(g, left, right)

        assert len(matching) == 2
        assert matching['A'] == 'X'
        assert matching['B'] == 'Y'

    def test_hopcroft_karp_complete_bipartite(self):
        """Test Hopcroft-Karp on complete bipartite graph."""
        g = Graph.builder().add_bipartite(['A', 'B'], ['X', 'Y', 'Z'], complete=True).build()

        left = {'A', 'B'}
        right = {'X', 'Y', 'Z'}

        matching = hopcroft_karp(g, left, right)

        # Should match all left vertices
        assert len(matching) == 2

    def test_hopcroft_karp_no_matching(self):
        """Test Hopcroft-Karp when no matching exists."""
        # No edges between partitions
        g = Graph.builder().add_bipartite(['A', 'B'], ['X', 'Y'], complete=False).build()

        left = {'A', 'B'}
        right = {'X', 'Y'}

        matching = hopcroft_karp(g, left, right)

        assert len(matching) == 0

    def test_maximum_bipartite_matching(self):
        """Test maximum_bipartite_matching."""
        g = Graph.builder().add_bipartite(['A', 'B'], ['X', 'Y'], complete=True).build()

        left = {'A', 'B'}
        right = {'X', 'Y'}

        matching = maximum_bipartite_matching(g, left, right)

        assert len(matching) == 2
        assert all(isinstance(edge, tuple) for edge in matching)

    def test_is_perfect_matching_true(self):
        """Test is_perfect_matching returns True."""
        g = Graph.builder().add_bipartite(['A', 'B'], ['X', 'Y'], complete=True).build()

        left = {'A', 'B'}
        right = {'X', 'Y'}

        assert is_perfect_matching(g, left, right) is True

    def test_is_perfect_matching_false_unequal_sizes(self):
        """Test is_perfect_matching with unequal partition sizes."""
        g = Graph.builder().add_bipartite(['A'], ['X', 'Y'], complete=True).build()

        left = {'A'}
        right = {'X', 'Y'}

        assert is_perfect_matching(g, left, right) is False

    def test_maximum_matching_bipartite(self):
        """Test maximum_matching on bipartite graph."""
        g = Graph.from_edges(('A', 'B'), ('C', 'D'), directed=False)

        matching = maximum_matching(g)

        assert len(matching) == 2

    def test_matching_size(self):
        """Test matching_size."""
        matching = {('A', 'B'), ('C', 'D')}

        assert matching_size(matching) == 2

    def test_is_maximal_matching_true(self):
        """Test is_maximal_matching returns True."""
        g = Graph.from_edges(('A', 'B'), ('C', 'D'), directed=False)
        matching = {('A', 'B'), ('C', 'D')}

        assert is_maximal_matching(g, matching) is True

    def test_is_maximal_matching_false(self):
        """Test is_maximal_matching returns False."""
        g = Graph.from_edges(('A', 'B'), ('C', 'D'), directed=False)
        matching = {('A', 'B')}

        assert is_maximal_matching(g, matching) is False


class TestColoring:
    """Tests for graph coloring algorithms."""

    def test_greedy_coloring_simple(self):
        """Test greedy coloring on simple graph."""
        # Triangle needs 3 colors
        g = Graph.builder().add_cycle('A', 'B', 'C', directed=False).build()

        coloring = greedy_coloring(g)

        assert len(coloring) == 3
        assert is_valid_coloring(g, coloring)

    def test_greedy_coloring_empty(self):
        """Test greedy coloring on empty graph."""
        g = Graph()

        coloring = greedy_coloring(g)

        assert coloring == {}

    def test_greedy_coloring_with_order(self):
        """Test greedy coloring with specified order."""
        g = Graph.from_edges(('A', 'B'), ('B', 'C'), directed=False)

        coloring = greedy_coloring(g, order=['A', 'B', 'C'])

        assert is_valid_coloring(g, coloring)

    def test_welsh_powell(self):
        """Test Welsh-Powell coloring."""
        # Complete graph K4 needs 4 colors
        g = Graph.builder().add_complete('A', 'B', 'C', 'D').build()

        coloring = welsh_powell(g)

        assert is_valid_coloring(g, coloring)
        # Complete graph needs n colors
        assert len(set(coloring.values())) == 4

    def test_chromatic_number_bipartite(self):
        """Test chromatic number on bipartite graph."""
        g = Graph.builder().add_bipartite(['A', 'B'], ['X', 'Y'], complete=True).build()

        chi = chromatic_number(g)

        # Bipartite graphs need exactly 2 colors
        assert chi == 2

    def test_chromatic_number_triangle(self):
        """Test chromatic number on triangle."""
        g = Graph.builder().add_cycle('A', 'B', 'C', directed=False).build()

        chi = chromatic_number(g)

        assert chi == 3

    def test_is_valid_coloring_valid(self):
        """Test is_valid_coloring with valid coloring."""
        g = Graph.from_edges(('A', 'B'), directed=False)
        coloring = {'A': 0, 'B': 1}

        assert is_valid_coloring(g, coloring) is True

    def test_is_valid_coloring_invalid(self):
        """Test is_valid_coloring with invalid coloring."""
        g = Graph.from_edges(('A', 'B'), directed=False)
        coloring = {'A': 0, 'B': 0}  # Same color for adjacent vertices

        assert is_valid_coloring(g, coloring) is False

    def test_dsatur(self):
        """Test DSatur coloring."""
        g = Graph.builder().add_cycle('A', 'B', 'C', 'D', directed=False).build()

        coloring = dsatur(g)

        assert is_valid_coloring(g, coloring)

    def test_edge_coloring(self):
        """Test edge coloring."""
        g = Graph.builder().add_path('A', 'B', 'C', directed=False).build()

        coloring = edge_coloring(g)

        # Path of 2 edges can be colored with 1 color (no adjacent edges)
        assert len(coloring) >= 2

    def test_chromatic_index(self):
        """Test chromatic index (edge chromatic number)."""
        # Star graph: center has degree 3, so chromatic index >= 3
        g = Graph.builder().add_star('center', 'A', 'B', 'C').build()

        chi_prime = chromatic_index(g)

        assert chi_prime >= 3

    def test_is_k_colorable_true(self):
        """Test is_k_colorable returns True."""
        # Bipartite graph is 2-colorable
        g = Graph.from_edges(('A', 'B'), directed=False)

        assert is_k_colorable(g, 2) is True

    def test_is_k_colorable_false(self):
        """Test is_k_colorable returns False (approximately)."""
        # Complete graph K4 needs 4 colors, not 2
        g = Graph.builder().add_complete('A', 'B', 'C', 'D').build()

        assert is_k_colorable(g, 2) is False

    def test_greedy_coloring_bipartite(self):
        """Test greedy coloring produces 2 colors for bipartite graph."""
        g = Graph.builder().add_bipartite(['A', 'B'], ['X', 'Y'], complete=True).build()

        coloring = greedy_coloring(g)

        # Should use exactly 2 colors for bipartite graph
        assert len(set(coloring.values())) == 2


class TestEdgeCases:
    """Tests for edge cases across all Phase 2 algorithms."""

    def test_centrality_single_vertex(self):
        """Test centrality on single vertex."""
        g = Graph.from_vertices('A')

        pr = pagerank(g)
        bc = betweenness_centrality(g)
        cc = closeness_centrality(g)
        dc = degree_centrality(g)

        assert pr['A'] == 1.0
        assert bc['A'] == 0.0
        assert cc['A'] == 0.0
        assert dc['A'] == 0.0

    def test_flow_zero_capacity(self):
        """Test flow with zero capacity edge."""
        g = Graph.from_edges(('S', 'T'), weight=0)

        flow_value = max_flow(g, 'S', 'T')

        assert flow_value == 0.0

    def test_matching_single_edge(self):
        """Test matching on single edge."""
        g = Graph.from_edges(('A', 'B'), directed=False)

        matching = maximum_matching(g)

        assert len(matching) == 1

    def test_coloring_single_vertex(self):
        """Test coloring single vertex."""
        g = Graph.from_vertices('A')

        coloring = greedy_coloring(g)

        assert coloring['A'] == 0
