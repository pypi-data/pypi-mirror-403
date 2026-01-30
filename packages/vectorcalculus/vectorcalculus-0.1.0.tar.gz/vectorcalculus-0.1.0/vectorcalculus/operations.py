"""Numerical vector calculus operators using finite differences.

Functions expect points as sequences (x, y) or (x, y, z).
Scalar fields: callable(point) -> float
Vector fields: callable(point) -> sequence of floats
"""
from typing import Sequence, Callable, Tuple, Any
from vectorcalculus.vector import Vector

_np: Any = None
try:
    import numpy as _np
except Exception:
    _np = None


def _ensure_point(p: Sequence[float]) -> Tuple[float, ...]:
    return tuple(float(x) for x in p)


def gradient(scalar_field: Callable[[Sequence[float]], float], point: Sequence[float], h: float = 1e-6) -> Vector:
    """Central-difference gradient returning a `Vector` for Python scalars."""
    p = _ensure_point(point)
    n = len(p)
    grad = []
    for i in range(n):
        forward = list(p)
        backward = list(p)
        forward[i] += h
        backward[i] -= h
        f1 = scalar_field(tuple(forward))
        f2 = scalar_field(tuple(backward))
        grad.append((f1 - f2) / (2 * h))
    return Vector(grad)


def divergence(vector_field: Callable[[Sequence[float]], Sequence[float]], point: Sequence[float], h: float = 1e-6) -> float:
    p = _ensure_point(point)
    n = len(p)
    div = 0.0
    for i in range(n):
        forward = list(p)
        backward = list(p)
        forward[i] += h
        backward[i] -= h
        f1 = vector_field(tuple(forward))[i]
        f2 = vector_field(tuple(backward))[i]
        div += (f1 - f2) / (2 * h)
    return float(div)


def curl(vector_field: Callable[[Sequence[float]], Sequence[float]], point: Sequence[float], h: float = 1e-6) -> Vector:
    p = _ensure_point(point)
    if len(p) != 3:
        raise TypeError("Curl is defined only in 3D for this implementation")
    def partial(component_index, var_index, sign):
        q = list(p)
        q[var_index] += sign * h
        return vector_field(tuple(q))[component_index]

    dFz_dy = (partial(2, 1, 1) - partial(2, 1, -1)) / (2 * h)
    dFy_dz = (partial(1, 2, 1) - partial(1, 2, -1)) / (2 * h)
    dFx_dz = (partial(0, 2, 1) - partial(0, 2, -1)) / (2 * h)
    dFz_dx = (partial(2, 0, 1) - partial(2, 0, -1)) / (2 * h)
    dFy_dx = (partial(1, 0, 1) - partial(1, 0, -1)) / (2 * h)
    dFx_dy = (partial(0, 1, 1) - partial(0, 1, -1)) / (2 * h)

    cx = dFz_dy - dFy_dz
    cy = dFx_dz - dFz_dx
    cz = dFy_dx - dFx_dy

    return Vector(cx, cy, cz)


def laplacian(scalar_field: Callable[[Sequence[float]], float], point: Sequence[float], h: float = 1e-4) -> float:
    p = _ensure_point(point)
    n = len(p)
    lap = 0.0
    base = scalar_field(tuple(p))
    for i in range(n):
        qf = list(p)
        qb = list(p)
        qf[i] += h
        qb[i] -= h
        lap += (scalar_field(tuple(qf)) - 2 * base + scalar_field(tuple(qb))) / (h * h)
    return float(lap)


# --- NumPy-accelerated versions (optional) ---
def gradient_np(scalar_field: Callable[..., Any], point: Sequence[float], h: float = 1e-6) -> Any:
    """Vectorized gradient using NumPy. Returns a NumPy array.

    The `scalar_field` must accept and return NumPy arrays when given NumPy inputs.
    """
    if _np is None:
        raise RuntimeError("NumPy is required for gradient_np")
    p = _np.asarray(point, dtype=float)
    n = p.size
    out = _np.empty(n, dtype=float)
    for i in range(n):
        e = _np.zeros_like(p)
        e[i] = h
        f1 = scalar_field(p + e)
        f2 = scalar_field(p - e)
        out[i] = (f1 - f2) / (2 * h)
    return out


def divergence_np(vector_field: Callable[..., Any], point: Sequence[float], h: float = 1e-6) -> float:
    if _np is None:
        raise RuntimeError("NumPy is required for divergence_np")
    p = _np.asarray(point, dtype=float)
    n = p.size
    div = 0.0
    for i in range(n):
        e = _np.zeros_like(p)
        e[i] = h
        f1 = vector_field(p + e)[i]
        f2 = vector_field(p - e)[i]
        div += (f1 - f2) / (2 * h)
    return float(div)


def curl_np(vector_field: Callable[..., Any], point: Sequence[float], h: float = 1e-6) -> Any:
    if _np is None:
        raise RuntimeError("NumPy is required for curl_np")
    p = _np.asarray(point, dtype=float)
    if p.size != 3:
        raise TypeError("curl_np requires 3D points")
    def partial(component_index: int, var_index: int, sign: int):
        e = _np.zeros_like(p)
        e[var_index] = sign * h
        return vector_field(p + e)[component_index]

    dFz_dy = (partial(2, 1, 1) - partial(2, 1, -1)) / (2 * h)
    dFy_dz = (partial(1, 2, 1) - partial(1, 2, -1)) / (2 * h)
    dFx_dz = (partial(0, 2, 1) - partial(0, 2, -1)) / (2 * h)
    dFz_dx = (partial(2, 0, 1) - partial(2, 0, -1)) / (2 * h)
    dFy_dx = (partial(1, 0, 1) - partial(1, 0, -1)) / (2 * h)
    dFx_dy = (partial(0, 1, 1) - partial(0, 1, -1)) / (2 * h)

    cx = dFz_dy - dFy_dz
    cy = dFx_dz - dFz_dx
    cz = dFy_dx - dFx_dy
    return _np.array([cx, cy, cz], dtype=float)


def laplacian_np(scalar_field: Callable[..., Any], point: Sequence[float], h: float = 1e-4) -> float:
    if _np is None:
        raise RuntimeError("NumPy is required for laplacian_np")
    p = _np.asarray(point, dtype=float)
    n = p.size
    base = scalar_field(p)
    lap = 0.0
    for i in range(n):
        e = _np.zeros_like(p)
        e[i] = h
        lap += (scalar_field(p + e) - 2 * base + scalar_field(p - e)) / (h * h)
    return float(lap)
