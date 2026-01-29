"""
Immutable Edge implementation for graphs.

Edges connect vertices and can be directed or undirected, weighted or unweighted.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Edge:
    """
    Immutable graph edge connecting two vertices.

    Edges can be directed or undirected and can carry attributes
    like weight, label, capacity, etc.

    Attributes:
        source: Source vertex ID
        target: Target vertex ID
        directed: Whether edge is directed (default: True)
        weight: Edge weight (default: 1.0)
        attrs: Dictionary of edge attributes

    Example:
        >>> e1 = Edge('A', 'B', weight=5.0)
        >>> e2 = Edge('A', 'B', directed=False)
        >>> e3 = e1.with_attrs(label='connection')
    """

    source: str
    target: str
    directed: bool = True
    weight: float = 1.0
    attrs: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure attrs is a dict."""
        if not isinstance(self.attrs, dict):
            object.__setattr__(self, 'attrs', dict(self.attrs))

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get attribute value.

        Args:
            key: Attribute key
            default: Default value if key not found

        Returns:
            Attribute value or default

        Example:
            >>> e = Edge('A', 'B', attrs={'capacity': 100})
            >>> e.get('capacity')
            100
        """
        return self.attrs.get(key, default)

    def with_attrs(self, **kwargs) -> 'Edge':
        """
        Create new edge with updated attributes.

        Args:
            **kwargs: Attributes to add/update

        Returns:
            New Edge with updated attributes

        Example:
            >>> e1 = Edge('A', 'B')
            >>> e2 = e1.with_attrs(label='highway', capacity=50)
            >>> e2.get('label')
            'highway'
        """
        new_attrs = {**self.attrs, **kwargs}
        return Edge(
            self.source,
            self.target,
            directed=self.directed,
            weight=self.weight,
            attrs=new_attrs
        )

    def with_weight(self, weight: float) -> 'Edge':
        """
        Create new edge with updated weight.

        Args:
            weight: New edge weight

        Returns:
            New Edge with updated weight

        Example:
            >>> e1 = Edge('A', 'B', weight=1.0)
            >>> e2 = e1.with_weight(5.0)
            >>> e2.weight
            5.0
        """
        return Edge(
            self.source,
            self.target,
            directed=self.directed,
            weight=weight,
            attrs=self.attrs
        )

    def reversed(self) -> 'Edge':
        """
        Create reversed edge (swap source and target).

        Returns:
            New Edge with source and target swapped

        Example:
            >>> e1 = Edge('A', 'B', weight=3.0)
            >>> e2 = e1.reversed()
            >>> e2.source
            'B'
            >>> e2.target
            'A'
        """
        return Edge(
            self.target,
            self.source,
            directed=self.directed,
            weight=self.weight,
            attrs=self.attrs
        )

    def to_undirected(self) -> 'Edge':
        """
        Create undirected version of edge.

        Returns:
            New Edge with directed=False

        Example:
            >>> e1 = Edge('A', 'B', directed=True)
            >>> e2 = e1.to_undirected()
            >>> e2.directed
            False
        """
        return Edge(
            self.source,
            self.target,
            directed=False,
            weight=self.weight,
            attrs=self.attrs
        )

    def to_directed(self) -> 'Edge':
        """
        Create directed version of edge.

        Returns:
            New Edge with directed=True

        Example:
            >>> e1 = Edge('A', 'B', directed=False)
            >>> e2 = e1.to_directed()
            >>> e2.directed
            True
        """
        return Edge(
            self.source,
            self.target,
            directed=True,
            weight=self.weight,
            attrs=self.attrs
        )

    def connects(self, v1: str, v2: str) -> bool:
        """
        Check if edge connects two vertices.

        For directed edges, order matters.
        For undirected edges, order doesn't matter.

        Args:
            v1: First vertex ID
            v2: Second vertex ID

        Returns:
            True if edge connects the vertices

        Example:
            >>> e1 = Edge('A', 'B', directed=True)
            >>> e1.connects('A', 'B')
            True
            >>> e1.connects('B', 'A')
            False
            >>> e2 = Edge('A', 'B', directed=False)
            >>> e2.connects('B', 'A')
            True
        """
        if self.directed:
            return self.source == v1 and self.target == v2
        else:
            return (self.source == v1 and self.target == v2) or \
                   (self.source == v2 and self.target == v1)

    def __repr__(self) -> str:
        """String representation."""
        arrow = '->' if self.directed else '<->'
        parts = [f"{self.source} {arrow} {self.target}"]

        if self.weight != 1.0:
            parts.append(f"weight={self.weight}")

        if self.attrs:
            attrs_str = ', '.join(f'{k}={v!r}' for k, v in self.attrs.items())
            parts.append(attrs_str)

        return f"Edge({', '.join(parts)})"

    def __str__(self) -> str:
        """Human-readable string."""
        arrow = '->' if self.directed else '<->'
        if self.weight != 1.0:
            return f"{self.source} {arrow} {self.target} ({self.weight})"
        return f"{self.source} {arrow} {self.target}"

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        if self.directed:
            return hash((self.source, self.target, self.directed))
        else:
            # For undirected edges, hash should be same regardless of order
            return hash((frozenset([self.source, self.target]), self.directed))

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, Edge):
            return False

        if self.directed != other.directed:
            return False

        if self.directed:
            # Directed: source and target must match exactly
            return (self.source == other.source and
                    self.target == other.target and
                    self.weight == other.weight and
                    self.attrs == other.attrs)
        else:
            # Undirected: can match in either direction
            match1 = (self.source == other.source and self.target == other.target)
            match2 = (self.source == other.target and self.target == other.source)
            return (match1 or match2) and \
                   self.weight == other.weight and \
                   self.attrs == other.attrs
