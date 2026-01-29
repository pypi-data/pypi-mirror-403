"""
Immutable Vertex (node) implementation for graphs.

Similar to AlgoTree's Node but designed for graphs where connections
are represented by explicit Edge objects rather than parent-child relationships.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Vertex:
    """
    Immutable graph vertex with attributes.

    A vertex represents a node in a graph. Unlike tree nodes, vertices
    don't maintain child relationships - those are managed by Edge objects
    in the Graph.

    Attributes:
        id: Unique identifier for the vertex
        attrs: Dictionary of vertex attributes

    Example:
        >>> v1 = Vertex('A', attrs={'value': 10})
        >>> v2 = v1.with_attrs(value=20)
        >>> v1.attrs['value']
        10
        >>> v2.attrs['value']
        20
    """

    id: str
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
            >>> v = Vertex('A', attrs={'x': 10})
            >>> v.get('x')
            10
            >>> v.get('y', 0)
            0
        """
        return self.attrs.get(key, default)

    def with_attrs(self, **kwargs) -> 'Vertex':
        """
        Create new vertex with updated attributes.

        Args:
            **kwargs: Attributes to add/update

        Returns:
            New Vertex with updated attributes

        Example:
            >>> v1 = Vertex('A', attrs={'x': 10})
            >>> v2 = v1.with_attrs(y=20, z=30)
            >>> v2.get('y')
            20
        """
        new_attrs = {**self.attrs, **kwargs}
        return Vertex(self.id, attrs=new_attrs)

    def without_attrs(self, *keys: str) -> 'Vertex':
        """
        Create new vertex without specified attributes.

        Args:
            *keys: Attribute keys to remove

        Returns:
            New Vertex without specified attributes

        Example:
            >>> v1 = Vertex('A', attrs={'x': 10, 'y': 20})
            >>> v2 = v1.without_attrs('y')
            >>> 'y' in v2.attrs
            False
        """
        new_attrs = {k: v for k, v in self.attrs.items() if k not in keys}
        return Vertex(self.id, attrs=new_attrs)

    def with_id(self, new_id: str) -> 'Vertex':
        """
        Create new vertex with different ID.

        Args:
            new_id: New vertex ID

        Returns:
            New Vertex with updated ID

        Example:
            >>> v1 = Vertex('A')
            >>> v2 = v1.with_id('B')
            >>> v2.id
            'B'
        """
        return Vertex(new_id, attrs=self.attrs)

    def __repr__(self) -> str:
        """String representation."""
        if self.attrs:
            attrs_str = ', '.join(f'{k}={v!r}' for k, v in self.attrs.items())
            return f"Vertex({self.id!r}, {attrs_str})"
        return f"Vertex({self.id!r})"

    def __str__(self) -> str:
        """Human-readable string."""
        return self.id

    def __hash__(self) -> int:
        """
        Hash based on ID only.

        Note: Hash is based on ID while equality considers both ID and attrs.
        This is intentional to allow vertices with the same ID to be treated
        as the same node in graph operations (sets, dicts), even if their
        attributes differ. For strict equality including attributes, compare
        vertices directly with ==.
        """
        return hash(self.id)

    def __eq__(self, other) -> bool:
        """Equality based on ID and attributes."""
        if not isinstance(other, Vertex):
            return False
        return self.id == other.id and self.attrs == other.attrs
