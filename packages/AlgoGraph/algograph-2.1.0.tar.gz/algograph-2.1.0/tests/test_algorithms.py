"""
Tests for graph algorithms.
"""

import pytest

from AlgoGraph import Vertex, Edge, Graph
from AlgoGraph.algorithms import (
    # Traversal
    dfs, bfs, topological_sort, has_cycle, find_path,
    # Shortest path
    dijkstra, bellman_ford, shortest_path, shortest_path_length,
    # Connectivity
    connected_components, is_connected, is_bipartite,
    strongly_connected_components,
    # Spanning tree
    kruskal, prim, minimum_spanning_tree, total_weight
)


class TestTraversal:
    """Tests for traversal algorithms."""

    def test_dfs_simple(self):
        """Test DFS on simple graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B'), Edge('B', 'C')}
        )

        order = dfs(g, 'A')
        assert order == ['A', 'B', 'C']

    def test_bfs_simple(self):
        """Test BFS on simple graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B'), Edge('A', 'C')}
        )

        order = bfs(g, 'A')
        assert 'A' == order[0]
        assert set(order[1:]) == {'B', 'C'}

    def test_topological_sort_dag(self):
        """Test topological sort on DAG."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C'), Vertex('D')},
            {Edge('A', 'B'), Edge('A', 'C'), Edge('B', 'D'), Edge('C', 'D')}
        )

        order = topological_sort(g)
        assert order.index('A') < order.index('B')
        assert order.index('A') < order.index('C')
        assert order.index('B') < order.index('D')
        assert order.index('C') < order.index('D')

    def test_topological_sort_cycle(self):
        """Test topological sort fails on cyclic graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B'), Edge('B', 'C'), Edge('C', 'A')}
        )

        with pytest.raises(ValueError, match="cycle"):
            topological_sort(g)

    def test_has_cycle_acyclic(self):
        """Test cycle detection on acyclic graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B'), Edge('B', 'C')}
        )

        assert not has_cycle(g)

    def test_has_cycle_cyclic(self):
        """Test cycle detection on cyclic graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B'), Edge('B', 'C'), Edge('C', 'A')}
        )

        assert has_cycle(g)

    def test_find_path_exists(self):
        """Test finding path that exists."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C'), Vertex('D')},
            {Edge('A', 'B'), Edge('B', 'C'), Edge('C', 'D')}
        )

        path = find_path(g, 'A', 'D')
        assert path == ['A', 'B', 'C', 'D']

    def test_find_path_not_exists(self):
        """Test finding path that doesn't exist."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B')}
        )

        path = find_path(g, 'A', 'C')
        assert path is None


class TestShortestPath:
    """Tests for shortest path algorithms."""

    def test_dijkstra_simple(self):
        """Test Dijkstra on simple graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B', weight=1.0), Edge('B', 'C', weight=2.0)}
        )

        distances, _ = dijkstra(g, 'A')
        assert distances['A'] == 0.0
        assert distances['B'] == 1.0
        assert distances['C'] == 3.0

    def test_dijkstra_shortest_path(self):
        """Test Dijkstra finds shortest path."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {
                Edge('A', 'B', weight=1.0),
                Edge('A', 'C', weight=4.0),
                Edge('B', 'C', weight=2.0)
            }
        )

        distances, _ = dijkstra(g, 'A')
        assert distances['C'] == 3.0  # A->B->C is shorter than A->C

    def test_bellman_ford_simple(self):
        """Test Bellman-Ford algorithm."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B', weight=-1.0), Edge('B', 'C', weight=2.0)}
        )

        distances, _ = bellman_ford(g, 'A')
        assert distances['A'] == 0.0
        assert distances['B'] == -1.0
        assert distances['C'] == 1.0

    def test_shortest_path_function(self):
        """Test shortest_path convenience function."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B', weight=1.0), Edge('B', 'C', weight=2.0)}
        )

        path = shortest_path(g, 'A', 'C')
        assert path == ['A', 'B', 'C']

    def test_shortest_path_length(self):
        """Test shortest_path_length function."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B', weight=2.0), Edge('B', 'C', weight=3.0)}
        )

        length = shortest_path_length(g, 'A', 'C')
        assert length == 5.0


class TestConnectivity:
    """Tests for connectivity algorithms."""

    def test_connected_components_single(self):
        """Test connected components on connected graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B', directed=False), Edge('B', 'C', directed=False)}
        )

        components = connected_components(g)
        assert len(components) == 1
        assert components[0] == {'A', 'B', 'C'}

    def test_connected_components_multiple(self):
        """Test connected components on disconnected graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C'), Vertex('D')},
            {Edge('A', 'B', directed=False), Edge('C', 'D', directed=False)}
        )

        components = connected_components(g)
        assert len(components) == 2
        assert {'A', 'B'} in components
        assert {'C', 'D'} in components

    def test_is_connected_true(self):
        """Test is_connected returns True for connected graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B'), Edge('B', 'C')}
        )

        assert is_connected(g)

    def test_is_connected_false(self):
        """Test is_connected returns False for disconnected graph."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B')}
        )

        # Graph has isolated vertex C
        assert not is_connected(g)

    def test_is_bipartite_true(self):
        """Test bipartite detection on bipartite graph."""
        # Square graph (bipartite)
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C'), Vertex('D')},
            {
                Edge('A', 'B', directed=False),
                Edge('B', 'C', directed=False),
                Edge('C', 'D', directed=False),
                Edge('D', 'A', directed=False)
            }
        )

        is_bip, coloring = is_bipartite(g)
        assert is_bip
        # Check coloring is valid
        assert coloring['A'] != coloring['B']
        assert coloring['B'] != coloring['C']
        assert coloring['C'] != coloring['D']
        assert coloring['D'] != coloring['A']

    def test_is_bipartite_false(self):
        """Test bipartite detection on non-bipartite graph."""
        # Triangle (not bipartite)
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {
                Edge('A', 'B', directed=False),
                Edge('B', 'C', directed=False),
                Edge('C', 'A', directed=False)
            }
        )

        is_bip, _ = is_bipartite(g)
        assert not is_bip

    def test_strongly_connected_components(self):
        """Test strongly connected components."""
        # Cycle: A -> B -> C -> A
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {Edge('A', 'B'), Edge('B', 'C'), Edge('C', 'A')}
        )

        sccs = strongly_connected_components(g)
        assert len(sccs) == 1
        assert sccs[0] == {'A', 'B', 'C'}


class TestSpanningTree:
    """Tests for spanning tree algorithms."""

    def test_kruskal_simple(self):
        """Test Kruskal's algorithm."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {
                Edge('A', 'B', weight=1.0, directed=False),
                Edge('B', 'C', weight=2.0, directed=False),
                Edge('A', 'C', weight=3.0, directed=False)
            }
        )

        mst = kruskal(g)
        assert mst.edge_count == 2  # |V| - 1
        assert total_weight(mst) == 3.0  # 1.0 + 2.0

    def test_prim_simple(self):
        """Test Prim's algorithm."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C')},
            {
                Edge('A', 'B', weight=1.0, directed=False),
                Edge('B', 'C', weight=2.0, directed=False),
                Edge('A', 'C', weight=3.0, directed=False)
            }
        )

        mst = prim(g)
        assert mst.edge_count == 2
        assert total_weight(mst) == 3.0

    def test_minimum_spanning_tree(self):
        """Test MST wrapper function."""
        g = Graph(
            {Vertex('A'), Vertex('B'), Vertex('C'), Vertex('D')},
            {
                Edge('A', 'B', weight=1.0, directed=False),
                Edge('B', 'C', weight=2.0, directed=False),
                Edge('C', 'D', weight=3.0, directed=False),
                Edge('A', 'D', weight=4.0, directed=False)
            }
        )

        mst_kruskal = minimum_spanning_tree(g, 'kruskal')
        mst_prim = minimum_spanning_tree(g, 'prim')

        assert mst_kruskal.edge_count == 3
        assert mst_prim.edge_count == 3
        # Both should have same total weight
        assert total_weight(mst_kruskal) == total_weight(mst_prim)

    def test_total_weight(self):
        """Test total_weight function."""
        g = Graph(
            {Vertex('A'), Vertex('B')},
            {Edge('A', 'B', weight=5.0)}
        )

        assert total_weight(g) == 5.0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_graph(self):
        """Test algorithms on empty graph."""
        g = Graph()

        assert is_connected(g)
        components = connected_components(g)
        assert len(components) == 0

    def test_single_vertex(self):
        """Test algorithms on single vertex."""
        g = Graph({Vertex('A')})

        assert is_connected(g)
        components = connected_components(g)
        assert len(components) == 1
        assert components[0] == {'A'}

    def test_self_loop(self):
        """Test handling of self-loops."""
        g = Graph(
            {Vertex('A')},
            {Edge('A', 'A')}
        )

        assert has_cycle(g)
