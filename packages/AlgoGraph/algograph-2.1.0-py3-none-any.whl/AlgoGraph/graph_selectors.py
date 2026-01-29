"""
Composable selector system for graph pattern matching.

This module provides a type-safe, composable selector system for vertices
and edges that can be combined using logical operators.

Inspired by AlgoTree's selector pattern, adapted for graph-specific queries.
"""

from typing import Any, Callable, Iterator, Optional, Union, List, Dict, Pattern, Set
from abc import ABC, abstractmethod
import re

from AlgoGraph.graph import Graph
from AlgoGraph.vertex import Vertex
from AlgoGraph.edge import Edge


class Selector(ABC):
    """
    Abstract base class for graph element selectors.

    Selectors can be composed using logical operators:
    - & for AND
    - | for OR
    - ~ for NOT
    - ^ for XOR
    """

    @abstractmethod
    def matches(self, element: Any, graph: Optional[Graph] = None) -> bool:
        """
        Check if element matches this selector.

        Args:
            element: Element to test (Vertex or Edge)
            graph: Optional graph context for structural queries

        Returns:
            True if element matches
        """
        pass

    def select(self, graph: Graph) -> Iterator[Any]:
        """
        Select all matching elements from graph.

        Args:
            graph: Graph to search

        Yields:
            Matching elements
        """
        raise NotImplementedError("Subclasses must implement select()")

    def first(self, graph: Graph) -> Optional[Any]:
        """
        Get first matching element or None.

        Args:
            graph: Graph to search

        Returns:
            First matching element or None
        """
        for element in self.select(graph):
            return element
        return None

    def count(self, graph: Graph) -> int:
        """
        Count matching elements.

        Args:
            graph: Graph to search

        Returns:
            Number of matching elements
        """
        return sum(1 for _ in self.select(graph))

    def exists(self, graph: Graph) -> bool:
        """
        Check if any element matches.

        Args:
            graph: Graph to search

        Returns:
            True if at least one element matches
        """
        return self.first(graph) is not None

    # Logical operators for composition

    def __and__(self, other: 'Selector') -> 'Selector':
        """Combine selectors with AND."""
        return AndSelector(self, other)

    def __or__(self, other: 'Selector') -> 'Selector':
        """Combine selectors with OR."""
        return OrSelector(self, other)

    def __invert__(self) -> 'Selector':
        """Negate selector."""
        return NotSelector(self)

    def __xor__(self, other: 'Selector') -> 'Selector':
        """Combine selectors with XOR (exclusive or)."""
        return XorSelector(self, other)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class VertexSelector(Selector):
    """
    Base class for vertex selectors.

    Provides vertex-specific selection methods.
    """

    def select(self, graph: Graph) -> Iterator[Vertex]:
        """Select matching vertices from graph."""
        for vertex in graph.vertices:
            if self.matches(vertex, graph):
                yield vertex

    def ids(self, graph: Graph) -> Set[str]:
        """
        Get IDs of matching vertices.

        Args:
            graph: Graph to search

        Returns:
            Set of vertex IDs
        """
        return {v.id for v in self.select(graph)}


class EdgeSelector(Selector):
    """
    Base class for edge selectors.

    Provides edge-specific selection methods.
    """

    def select(self, graph: Graph) -> Iterator[Edge]:
        """Select matching edges from graph."""
        for edge in graph.edges:
            if self.matches(edge, graph):
                yield edge


# Logical combinators

class AndSelector(Selector):
    """Logical AND of two selectors."""

    def __init__(self, left: Selector, right: Selector):
        self.left = left
        self.right = right
        # Inherit type from left selector
        if isinstance(left, VertexSelector):
            self.__class__ = type('AndVertexSelector', (AndSelector, VertexSelector), {})
        elif isinstance(left, EdgeSelector):
            self.__class__ = type('AndEdgeSelector', (AndSelector, EdgeSelector), {})

    def matches(self, element: Any, graph: Optional[Graph] = None) -> bool:
        return self.left.matches(element, graph) and self.right.matches(element, graph)

    def select(self, graph: Graph) -> Iterator[Any]:
        # Use the first selector's select method, then filter
        for element in self.left.select(graph):
            if self.right.matches(element, graph):
                yield element

    def __repr__(self) -> str:
        return f"({self.left} & {self.right})"


class OrSelector(Selector):
    """Logical OR of two selectors."""

    def __init__(self, left: Selector, right: Selector):
        self.left = left
        self.right = right
        # Inherit type from left selector
        if isinstance(left, VertexSelector):
            self.__class__ = type('OrVertexSelector', (OrSelector, VertexSelector), {})
        elif isinstance(left, EdgeSelector):
            self.__class__ = type('OrEdgeSelector', (OrSelector, EdgeSelector), {})

    def matches(self, element: Any, graph: Optional[Graph] = None) -> bool:
        return self.left.matches(element, graph) or self.right.matches(element, graph)

    def select(self, graph: Graph) -> Iterator[Any]:
        # Get elements from both selectors, deduplicate
        seen = set()
        for element in self.left.select(graph):
            elem_id = element.id if isinstance(element, Vertex) else (element.source, element.target)
            if elem_id not in seen:
                seen.add(elem_id)
                yield element
        for element in self.right.select(graph):
            elem_id = element.id if isinstance(element, Vertex) else (element.source, element.target)
            if elem_id not in seen:
                seen.add(elem_id)
                yield element

    def __repr__(self) -> str:
        return f"({self.left} | {self.right})"


class NotSelector(Selector):
    """Logical NOT of a selector."""

    def __init__(self, selector: Selector):
        self.selector = selector
        # Inherit type from selector
        if isinstance(selector, VertexSelector):
            self.__class__ = type('NotVertexSelector', (NotSelector, VertexSelector), {})
        elif isinstance(selector, EdgeSelector):
            self.__class__ = type('NotEdgeSelector', (NotSelector, EdgeSelector), {})

    def matches(self, element: Any, graph: Optional[Graph] = None) -> bool:
        return not self.selector.matches(element, graph)

    def select(self, graph: Graph) -> Iterator[Any]:
        # Get all elements, filter out matches
        all_elements = list(graph.vertices) if isinstance(self.selector, VertexSelector) else list(graph.edges)
        for element in all_elements:
            if not self.selector.matches(element, graph):
                yield element

    def __repr__(self) -> str:
        return f"~{self.selector}"


class XorSelector(Selector):
    """Logical XOR of two selectors."""

    def __init__(self, left: Selector, right: Selector):
        self.left = left
        self.right = right
        # Inherit type from left selector
        if isinstance(left, VertexSelector):
            self.__class__ = type('XorVertexSelector', (XorSelector, VertexSelector), {})
        elif isinstance(left, EdgeSelector):
            self.__class__ = type('XorEdgeSelector', (XorSelector, EdgeSelector), {})

    def matches(self, element: Any, graph: Optional[Graph] = None) -> bool:
        left_match = self.left.matches(element, graph)
        right_match = self.right.matches(element, graph)
        return left_match != right_match

    def select(self, graph: Graph) -> Iterator[Any]:
        # Elements matching exactly one selector
        left_matches = set(self.left.select(graph))
        right_matches = set(self.right.select(graph))
        for element in left_matches ^ right_matches:
            yield element

    def __repr__(self) -> str:
        return f"({self.left} ^ {self.right})"


# Vertex selectors

class VertexIdSelector(VertexSelector):
    """Select vertices by ID pattern."""

    def __init__(self, pattern: str):
        """
        Create ID selector.

        Args:
            pattern: Glob pattern or regex for vertex IDs

        Example:
            >>> sel = VertexIdSelector('user_*')  # Glob pattern
            >>> sel = VertexIdSelector('user_\\d+')  # Regex pattern
        """
        self.pattern = pattern
        self._is_regex = bool(re.search(r'[\\^$+?{}[\]|()\s]', pattern))

        if self._is_regex:
            self._regex = re.compile(pattern)
            self._match_fn = lambda id: bool(self._regex.match(id))
        else:
            # Use glob-style matching
            import fnmatch
            self._match_fn = lambda id: fnmatch.fnmatch(id, pattern)

    def matches(self, element: Vertex, graph: Optional[Graph] = None) -> bool:
        return self._match_fn(element.id)

    def __repr__(self) -> str:
        return f"VertexIdSelector({self.pattern!r})"


class VertexAttrsSelector(VertexSelector):
    """Select vertices by attribute values."""

    def __init__(self, **attrs):
        """
        Create attribute selector.

        Args:
            **attrs: Attribute name/value pairs or callables

        Example:
            >>> sel = VertexAttrsSelector(age=30, city='NYC')
            >>> sel = VertexAttrsSelector(age=lambda a: a > 30)
        """
        self.attrs = attrs

    def matches(self, element: Vertex, graph: Optional[Graph] = None) -> bool:
        for key, expected in self.attrs.items():
            actual = element.get(key)

            if callable(expected):
                if not expected(actual):
                    return False
            else:
                if actual != expected:
                    return False

        return True

    def __repr__(self) -> str:
        return f"VertexAttrsSelector({self.attrs})"


class VertexDegreeSelector(VertexSelector):
    """Select vertices by degree."""

    def __init__(
        self,
        min_degree: Optional[int] = None,
        max_degree: Optional[int] = None,
        exact: Optional[int] = None
    ):
        """
        Create degree selector.

        Args:
            min_degree: Minimum degree (inclusive)
            max_degree: Maximum degree (inclusive)
            exact: Exact degree

        Example:
            >>> sel = VertexDegreeSelector(min_degree=5)
            >>> sel = VertexDegreeSelector(exact=3)
        """
        self.min_degree = min_degree
        self.max_degree = max_degree
        self.exact = exact

    def matches(self, element: Vertex, graph: Optional[Graph] = None) -> bool:
        if graph is None:
            raise ValueError("VertexDegreeSelector requires graph context")

        degree = graph.degree(element.id)

        if self.exact is not None:
            return degree == self.exact
        if self.min_degree is not None and degree < self.min_degree:
            return False
        if self.max_degree is not None and degree > self.max_degree:
            return False

        return True

    def __repr__(self) -> str:
        if self.exact is not None:
            return f"VertexDegreeSelector(exact={self.exact})"
        return f"VertexDegreeSelector(min={self.min_degree}, max={self.max_degree})"


class VertexNeighborSelector(VertexSelector):
    """Select vertices that have neighbors matching a selector."""

    def __init__(self, neighbor_selector: VertexSelector):
        """
        Create neighbor selector.

        Args:
            neighbor_selector: Selector for neighbors

        Example:
            >>> sel = VertexNeighborSelector(VertexAttrsSelector(active=True))
        """
        self.neighbor_selector = neighbor_selector

    def matches(self, element: Vertex, graph: Optional[Graph] = None) -> bool:
        if graph is None:
            raise ValueError("VertexNeighborSelector requires graph context")

        for neighbor_id in graph.neighbors(element.id):
            neighbor = graph.get_vertex(neighbor_id)
            if neighbor and self.neighbor_selector.matches(neighbor, graph):
                return True

        return False

    def __repr__(self) -> str:
        return f"VertexNeighborSelector({self.neighbor_selector})"


# Edge selectors

class EdgeSourceSelector(EdgeSelector):
    """Select edges by source vertex."""

    def __init__(self, source_selector: VertexSelector):
        """
        Create source selector.

        Args:
            source_selector: Selector for source vertices

        Example:
            >>> sel = EdgeSourceSelector(VertexIdSelector('A'))
        """
        self.source_selector = source_selector

    def matches(self, element: Edge, graph: Optional[Graph] = None) -> bool:
        if graph is None:
            raise ValueError("EdgeSourceSelector requires graph context")

        source_vertex = graph.get_vertex(element.source)
        if source_vertex is None:
            return False

        return self.source_selector.matches(source_vertex, graph)

    def __repr__(self) -> str:
        return f"EdgeSourceSelector({self.source_selector})"


class EdgeTargetSelector(EdgeSelector):
    """Select edges by target vertex."""

    def __init__(self, target_selector: VertexSelector):
        """
        Create target selector.

        Args:
            target_selector: Selector for target vertices
        """
        self.target_selector = target_selector

    def matches(self, element: Edge, graph: Optional[Graph] = None) -> bool:
        if graph is None:
            raise ValueError("EdgeTargetSelector requires graph context")

        target_vertex = graph.get_vertex(element.target)
        if target_vertex is None:
            return False

        return self.target_selector.matches(target_vertex, graph)

    def __repr__(self) -> str:
        return f"EdgeTargetSelector({self.target_selector})"


class EdgeWeightSelector(EdgeSelector):
    """Select edges by weight."""

    def __init__(
        self,
        min_weight: Optional[float] = None,
        max_weight: Optional[float] = None,
        exact: Optional[float] = None
    ):
        """
        Create weight selector.

        Args:
            min_weight: Minimum weight (inclusive)
            max_weight: Maximum weight (inclusive)
            exact: Exact weight
        """
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.exact = exact

    def matches(self, element: Edge, graph: Optional[Graph] = None) -> bool:
        weight = element.weight

        if self.exact is not None:
            return abs(weight - self.exact) < 1e-9
        if self.min_weight is not None and weight < self.min_weight:
            return False
        if self.max_weight is not None and weight > self.max_weight:
            return False

        return True

    def __repr__(self) -> str:
        if self.exact is not None:
            return f"EdgeWeightSelector(exact={self.exact})"
        return f"EdgeWeightSelector(min={self.min_weight}, max={self.max_weight})"


class EdgeDirectedSelector(EdgeSelector):
    """Select edges by directionality."""

    def __init__(self, directed: bool = True):
        """
        Create directionality selector.

        Args:
            directed: True for directed edges, False for undirected
        """
        self.directed = directed

    def matches(self, element: Edge, graph: Optional[Graph] = None) -> bool:
        return element.directed == self.directed

    def __repr__(self) -> str:
        return f"EdgeDirectedSelector(directed={self.directed})"


class EdgeAttrsSelector(EdgeSelector):
    """Select edges by attribute values."""

    def __init__(self, **attrs):
        """
        Create attribute selector.

        Args:
            **attrs: Attribute name/value pairs or callables
        """
        self.attrs = attrs

    def matches(self, element: Edge, graph: Optional[Graph] = None) -> bool:
        for key, expected in self.attrs.items():
            actual = element.get(key)

            if callable(expected):
                if not expected(actual):
                    return False
            else:
                if actual != expected:
                    return False

        return True

    def __repr__(self) -> str:
        return f"EdgeAttrsSelector({self.attrs})"


# Fluent selector builders

class VertexSelectorBuilder:
    """
    Fluent builder for vertex selectors.

    Provides convenient methods for constructing complex selectors.
    """

    def id(self, pattern: str) -> VertexIdSelector:
        """Select by ID pattern."""
        return VertexIdSelector(pattern)

    def attrs(self, **attrs) -> VertexAttrsSelector:
        """Select by attributes."""
        return VertexAttrsSelector(**attrs)

    def degree(
        self,
        min_degree: Optional[int] = None,
        max_degree: Optional[int] = None,
        exact: Optional[int] = None
    ) -> VertexDegreeSelector:
        """Select by degree."""
        return VertexDegreeSelector(min_degree, max_degree, exact)

    def has_neighbor(self, neighbor_selector: VertexSelector) -> VertexNeighborSelector:
        """Select vertices with matching neighbors."""
        return VertexNeighborSelector(neighbor_selector)


class EdgeSelectorBuilder:
    """
    Fluent builder for edge selectors.

    Provides convenient methods for constructing complex selectors.
    """

    def source(self, source_selector: VertexSelector) -> EdgeSourceSelector:
        """Select by source vertex."""
        return EdgeSourceSelector(source_selector)

    def target(self, target_selector: VertexSelector) -> EdgeTargetSelector:
        """Select by target vertex."""
        return EdgeTargetSelector(target_selector)

    def weight(
        self,
        min_weight: Optional[float] = None,
        max_weight: Optional[float] = None,
        exact: Optional[float] = None
    ) -> EdgeWeightSelector:
        """Select by weight."""
        return EdgeWeightSelector(min_weight, max_weight, exact)

    def directed(self, directed: bool = True) -> EdgeDirectedSelector:
        """Select by directionality."""
        return EdgeDirectedSelector(directed)

    def attrs(self, **attrs) -> EdgeAttrsSelector:
        """Select by attributes."""
        return EdgeAttrsSelector(**attrs)


# Module-level convenience instances
vertex = VertexSelectorBuilder()
edge = EdgeSelectorBuilder()
