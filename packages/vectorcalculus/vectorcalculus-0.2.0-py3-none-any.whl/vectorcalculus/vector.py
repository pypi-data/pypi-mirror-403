from math import sqrt, acos
from typing import Iterable, Tuple, Iterator, Any


class Vector:
    """Simple immutable vector class.

    Examples:
        v = Vector(1, 2, 3)
        u = Vector([0, 1, 0])
    """

    def __init__(self, *components: Any) -> None:
        # allow passing an iterable as single arg
        if len(components) == 1 and isinstance(components[0], Iterable):
            comps = tuple(float(x) for x in components[0])
        else:
            comps = tuple(float(x) for x in components)
        if len(comps) == 0:
            raise ValueError("Vector must have at least one component")
        self._c: Tuple[float, ...] = comps

    @property
    def components(self) -> Tuple[float, ...]:
        return self._c

    def __len__(self) -> int:
        return len(self._c)

    def __repr__(self):
        return f"Vector({', '.join(repr(x) for x in self._c)})"

    def __iter__(self) -> Iterator[float]:
        return iter(self._c)

    def __add__(self, other: 'Vector') -> 'Vector':
        if not isinstance(other, Vector) or len(other) != len(self):
            raise TypeError("Can only add vectors of same dimension")
        return Vector(a + b for a, b in zip(self._c, other._c))

    def __sub__(self, other: 'Vector') -> 'Vector':
        if not isinstance(other, Vector) or len(other) != len(self):
            raise TypeError("Can only subtract vectors of same dimension")
        return Vector(a - b for a, b in zip(self._c, other._c))

    def __mul__(self, scalar: float) -> 'Vector':
        return Vector(a * float(scalar) for a in self._c)

    def __rmul__(self, scalar: float) -> 'Vector':
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> 'Vector':
        s = float(scalar)
        if s == 0:
            raise ZeroDivisionError
        return Vector(a / s for a in self._c)

    def dot(self, other: 'Vector') -> float:
        if not isinstance(other, Vector) or len(other) != len(self):
            raise TypeError("Dot product requires vectors of same dimension")
        return sum(a * b for a, b in zip(self._c, other._c))

    def norm(self) -> float:
        return sqrt(sum(a * a for a in self._c))

    def normalize(self) -> 'Vector':
        n = self.norm()
        if n == 0:
            raise ValueError("Cannot normalize zero vector")
        return self / n

    def angle_with(self, other: 'Vector') -> float:
        """Return angle in radians between vectors."""
        d = self.dot(other)
        denom = self.norm() * other.norm()
        if denom == 0:
            raise ValueError("Angle undefined for zero vector")
        # clamp for numeric stability
        v = max(-1.0, min(1.0, d / denom))
        return acos(v)

    def proj_onto(self, other: 'Vector') -> 'Vector':
        """Projection of self onto other (vector)."""
        if other.norm() == 0:
            raise ValueError("Projection onto zero vector")
        coef = self.dot(other) / other.dot(other)
        return coef * other

    def cross(self, other: 'Vector') -> 'Vector':
        if len(self) != 3 or len(other) != 3:
            raise TypeError("Cross product defined only for 3D vectors")
        a1, a2, a3 = self._c
        b1, b2, b3 = other._c
        return Vector(a2 * b3 - a3 * b2, a3 * b1 - a1 * b3, a1 * b2 - a2 * b1)

    def to_list(self) -> list[float]:
        return list(self._c)
